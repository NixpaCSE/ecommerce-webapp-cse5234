"""BobaBox inventory and order Lambda.

Paste this file into the AWS Lambda console (Python 3.12). The handler name
is lambda_handler. Attach this same function, with Lambda proxy integration
on, to:

  GET  /inventory-management/inventory
  GET  /inventory-management/inventory/items/{id}
  GET  /inventory-management/inventory/items        (?name=)
  POST /order-processing/order

Reads and writes RDS MySQL. Set DB_HOST, DB_PORT, DB_NAME, DB_USER, and
DB_PASSWORD on the function. PyMySQL is not part of the Lambda runtime;
attach a layer that contains it before testing.

ITEM is matched on its primary key. The confirmation number returned to the
client is BBA- plus the new CUSTOMER_ORDER.ID. ITEM.IMAGE_URL holds the public
S3 URL for each kit photo. ITEM has no gradient column, so that field is empty.
"""

import base64
import json
import os

try:
    import pymysql
except ImportError:  # The console editor cannot bundle this package.
    pymysql = None

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}

_connection = None


def respond(status, payload):
    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": json.dumps(payload),
    }


def get_connection():
    global _connection
    if pymysql is None:
        raise RuntimeError("PyMySQL is not installed. Attach a Lambda layer that contains it.")

    if _connection is not None:
        try:
            _connection.ping(reconnect=True)
            return _connection
        except pymysql.MySQLError:
            _connection = None

    _connection = pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
        autocommit=False,
    )
    return _connection


def rollback_quietly(connection):
    try:
        connection.rollback()
    except pymysql.MySQLError:
        pass


def to_item(row):
    return {
        "id": str(row["ID"]),
        "itemNumber": row["ITEM_NUMBER"],
        "name": row["NAME"] or "",
        "description": row["DESCRIPTION"] or "",
        "price": float(row["UNIT_PRICE"] or 0),
        "quantity": int(row["AVAILABLE_QUANTITY"] or 0),
        "image": row["IMAGE_URL"] or "",
        "gradient": "",
    }


def parse_item_id(raw_id):
    try:
        return int(raw_id)
    except (TypeError, ValueError):
        return None


def get_inventory(connection, event):
    try:
        return read_inventory(connection, event)
    finally:
        # Reads run inside a transaction when autocommit is off. Close it
        # so a later order does not reuse this snapshot.
        rollback_quietly(connection)


def read_inventory(connection, event):
    path_params = event.get("pathParameters") or {}
    query = event.get("queryStringParameters") or {}
    item_id = path_params.get("id")
    name = query.get("name")

    with connection.cursor() as cursor:
        if item_id:
            parsed_id = parse_item_id(item_id)
            if parsed_id is None:
                return respond(400, {"message": "Invalid item id"})
            cursor.execute(
                """
                SELECT ID, ITEM_NUMBER, NAME, DESCRIPTION, AVAILABLE_QUANTITY, UNIT_PRICE, IMAGE_URL
                FROM ITEM
                WHERE ID = %s
                """,
                (parsed_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return respond(404, {"message": "Item not found"})
            return respond(200, to_item(row))

        if name:
            needle = name.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            cursor.execute(
                """
                SELECT ID, ITEM_NUMBER, NAME, DESCRIPTION, AVAILABLE_QUANTITY, UNIT_PRICE, IMAGE_URL
                FROM ITEM
                WHERE LOWER(NAME) LIKE %s ESCAPE '\\\\'
                ORDER BY ID
                """,
                (f"%{needle.lower()}%",),
            )
            return respond(200, [to_item(row) for row in cursor.fetchall()])

        cursor.execute(
            """
            SELECT ID, ITEM_NUMBER, NAME, DESCRIPTION, AVAILABLE_QUANTITY, UNIT_PRICE, IMAGE_URL
            FROM ITEM
            ORDER BY ID
            """
        )
        return respond(200, [to_item(row) for row in cursor.fetchall()])


def parse_body(event):
    body = event.get("body")
    if event.get("isBase64Encoded") and isinstance(body, str):
        body = base64.b64decode(body).decode("utf-8")
    if body is None or body == "":
        return {}
    if isinstance(body, dict):
        return body
    return json.loads(body)


def field(source, *names):
    for name in names:
        value = source.get(name)
        if value is not None:
            return str(value)
    return ""


def place_order(connection, event):
    try:
        order = parse_body(event)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return respond(400, {"message": "Order body must be JSON"})

    lines = order.get("items") or []
    payment = order.get("payment") or {}
    shipping = order.get("shipping") or {}

    if not lines:
        return respond(400, {"message": "Order has no items"})
    if not payment or not shipping:
        return respond(400, {"message": "Order requires payment and shipping"})

    requested = {}
    for line in lines:
        item_id = parse_item_id(line.get("id"))
        if item_id is None:
            return respond(400, {"message": f"Invalid item id {line.get('id')}"})
        try:
            quantity = int(line.get("quantity", 0))
        except (TypeError, ValueError):
            return respond(400, {"message": f"Invalid quantity for item {item_id}"})
        if quantity <= 0:
            return respond(400, {"message": f"Quantity for item {item_id} must be at least 1"})
        requested[item_id] = requested.get(item_id, 0) + quantity

    connection.begin()
    try:
        with connection.cursor() as cursor:
            ordered = []
            total = 0.0
            for item_id, quantity in requested.items():
                cursor.execute(
                    """
                    SELECT ID, ITEM_NUMBER, NAME, UNIT_PRICE, AVAILABLE_QUANTITY
                    FROM ITEM
                    WHERE ID = %s
                    FOR UPDATE
                    """,
                    (item_id,),
                )
                item = cursor.fetchone()
                if item is None:
                    connection.rollback()
                    return respond(404, {"message": "Item not found", "itemId": str(item_id)})

                available = int(item["AVAILABLE_QUANTITY"] or 0)
                if quantity > available:
                    connection.rollback()
                    return respond(409, {
                        "message": "Insufficient quantity",
                        "itemId": str(item["ID"]),
                        "name": item["NAME"],
                        "requested": quantity,
                        "available": available,
                    })

                updated = cursor.execute(
                    """
                    UPDATE ITEM
                    SET AVAILABLE_QUANTITY = AVAILABLE_QUANTITY - %s
                    WHERE ID = %s AND AVAILABLE_QUANTITY >= %s
                    """,
                    (quantity, item_id, quantity),
                )
                if updated != 1:
                    connection.rollback()
                    return respond(409, {
                        "message": "Insufficient quantity",
                        "itemId": str(item["ID"]),
                        "name": item["NAME"],
                        "requested": quantity,
                        "available": available,
                    })

                price = float(item["UNIT_PRICE"] or 0)
                ordered.append({
                    "id": str(item["ID"]),
                    "name": item["NAME"] or "",
                    "price": price,
                    "quantity": quantity,
                    "item_number": item["ITEM_NUMBER"] if item["ITEM_NUMBER"] is not None else item["ID"],
                })
                total = round(total + price * quantity, 2)

            cursor.execute(
                """
                INSERT INTO SHIPPING_INFO
                    (ADDRESS1, ADDRESS2, CITY, STATE, COUNTRY, POSTAL_CODE, EMAIL)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    field(shipping, "addressLine1", "address1"),
                    field(shipping, "addressLine2", "address2"),
                    field(shipping, "city"),
                    field(shipping, "state"),
                    field(shipping, "country") or "United States",
                    field(shipping, "zip", "postalCode", "postal_code"),
                    field(shipping, "email"),
                ),
            )
            shipping_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO PAYMENT_INFO (HOLDER_NAME, CARD_NUM, EXP_DATE, CVV)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    field(payment, "cardHolderName", "holderName"),
                    field(payment, "creditCardNumber", "cardNumber"),
                    field(payment, "expirationDate", "expDate"),
                    field(payment, "cvvCode", "cvv"),
                ),
            )
            payment_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO CUSTOMER_ORDER
                    (CUSTOMER_NAME, CUSTOMER_EMAIL, SHIPPING_INFO_ID_FK, PAYMENT_INFO_ID_FK, STATUS)
                VALUES (%s, %s, %s, %s, 'New')
                """,
                (
                    field(shipping, "name", "customerName"),
                    field(shipping, "email"),
                    shipping_id,
                    payment_id,
                ),
            )
            order_id = cursor.lastrowid

            for line in ordered:
                cursor.execute(
                    """
                    INSERT INTO CUSTOMER_ORDER_LINE_ITEM
                        (ITEM_NUMBER, ITEM_NAME, QUANTITY, CUSTOMER_ORDER_ID_FK)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (line["item_number"], line["name"], line["quantity"], order_id),
                )

        connection.commit()
    except Exception:
        rollback_quietly(connection)
        raise

    card = field(payment, "creditCardNumber", "cardNumber")
    return respond(200, {
        "confirmationNumber": f"BBA-{order_id}",
        "items": [
            {
                "id": line["id"],
                "name": line["name"],
                "price": line["price"],
                "quantity": line["quantity"],
            }
            for line in ordered
        ],
        "total": total,
        "shipping": shipping,
        "cardLast4": card[-4:] if card else "",
    })


def lambda_handler(event, context):
    method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
        or ""
    ).upper()

    if method == "OPTIONS":
        return respond(200, {})

    if pymysql is None:
        return respond(500, {"message": "PyMySQL is not installed on this function"})

    try:
        connection = get_connection()
        rollback_quietly(connection)
        if method == "GET":
            return get_inventory(connection, event)
        if method == "POST":
            return place_order(connection, event)
        return respond(405, {"message": "Method not allowed"})
    except KeyError as exc:
        print(f"Missing database setting: {exc}")
        return respond(500, {"message": f"Missing value: {exc}"})
    except Exception as exc:
        print(f"Request failed: {type(exc).__name__}: {exc}")
        return respond(500, {"message": f"{type(exc).__name__}: {exc}"})
