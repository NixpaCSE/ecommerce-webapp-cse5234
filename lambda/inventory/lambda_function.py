"""BobaBox inventory Lambda.

Paste this file into its own AWS Lambda function (Python 3.12). The handler
name is lambda_handler. Attach this function, with Lambda proxy integration
on, to:

  GET  /inventory-management/inventory
  GET  /inventory-management/inventory/items/{id}
  GET  /inventory-management/inventory/items        (?name=)
  POST /inventory-management/inventory/reserve
  POST /inventory-management/inventory/release

The storefront calls the GET routes. The order Lambda calls reserve when a
customer checks out, and release if that checkout fails after stock was
taken. This function is the only one that reads or writes ITEM.

Reserve body: {"items": [{"id": 1, "quantity": 2}]}
Reserve response: {"items": [{"id", "itemNumber", "name", "price", "quantity"}], "total"}
A line that asks for more than AVAILABLE_QUANTITY returns 409 and changes
nothing. Release adds the same quantities back.

Set DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD. PyMySQL is not part
of the Lambda runtime; attach a layer that contains it.

ITEM.IMAGE_URL holds the public S3 URL for each kit photo. ITEM has no
gradient column, so that response field is an empty string.
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


def parse_body(event):
    body = event.get("body")
    if event.get("isBase64Encoded") and isinstance(body, str):
        body = base64.b64decode(body).decode("utf-8")
    if body is None or body == "":
        return {}
    if isinstance(body, dict):
        return body
    return json.loads(body)


def path_segments(event):
    chunks = []
    for key in ("path", "rawPath", "resource"):
        value = event.get(key)
        if isinstance(value, str):
            chunks.append(value)
    params = event.get("pathParameters") or {}
    for key in ("proxy", "action"):
        value = params.get(key)
        if value:
            chunks.append(str(value))
    segments = []
    for chunk in chunks:
        segments.extend(
            part for part in chunk.lower().split("/")
            if part and not part.startswith("{")
        )
    return segments


def get_inventory(connection, event):
    try:
        return read_inventory(connection, event)
    finally:
        # Reads run inside a transaction when autocommit is off. Close it
        # so a later reserve does not reuse this snapshot.
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


def collect_lines(lines):
    if not lines:
        return None, respond(400, {"message": "Request has no items"})

    requested = {}
    for line in lines:
        item_id = parse_item_id(line.get("id"))
        if item_id is None:
            return None, respond(400, {"message": f"Invalid item id {line.get('id')}"})
        try:
            quantity = int(line.get("quantity", 0))
        except (TypeError, ValueError):
            return None, respond(400, {"message": f"Invalid quantity for item {item_id}"})
        if quantity <= 0:
            return None, respond(400, {"message": f"Quantity for item {item_id} must be at least 1"})
        requested[item_id] = requested.get(item_id, 0) + quantity
    return requested, None


def lock_item(cursor, item_id):
    cursor.execute(
        """
        SELECT ID, ITEM_NUMBER, NAME, UNIT_PRICE, AVAILABLE_QUANTITY
        FROM ITEM
        WHERE ID = %s
        FOR UPDATE
        """,
        (item_id,),
    )
    return cursor.fetchone()


def reserve_stock(connection, event):
    try:
        body = parse_body(event)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return respond(400, {"message": "Request body must be JSON"})

    requested, error = collect_lines(body.get("items") or [])
    if error:
        return error

    connection.begin()
    try:
        priced = []
        total = 0.0
        with connection.cursor() as cursor:
            for item_id, quantity in requested.items():
                item = lock_item(cursor, item_id)
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
                priced.append({
                    "id": str(item["ID"]),
                    "itemNumber": item["ITEM_NUMBER"] if item["ITEM_NUMBER"] is not None else item["ID"],
                    "name": item["NAME"] or "",
                    "price": price,
                    "quantity": quantity,
                })
                total = round(total + price * quantity, 2)

        connection.commit()
    except Exception:
        rollback_quietly(connection)
        raise

    return respond(200, {"items": priced, "total": total})


def release_stock(connection, event):
    """Put reserved units back. Used when the order service cannot finish checkout."""
    try:
        body = parse_body(event)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return respond(400, {"message": "Request body must be JSON"})

    requested, error = collect_lines(body.get("items") or [])
    if error:
        return error

    connection.begin()
    try:
        released = []
        with connection.cursor() as cursor:
            for item_id, quantity in requested.items():
                item = lock_item(cursor, item_id)
                if item is None:
                    connection.rollback()
                    return respond(404, {"message": "Item not found", "itemId": str(item_id)})

                updated = cursor.execute(
                    """
                    UPDATE ITEM
                    SET AVAILABLE_QUANTITY = AVAILABLE_QUANTITY + %s
                    WHERE ID = %s
                    """,
                    (quantity, item_id),
                )
                if updated != 1:
                    connection.rollback()
                    return respond(404, {"message": "Item not found", "itemId": str(item_id)})

                released.append({"id": str(item["ID"]), "quantity": quantity})

        connection.commit()
    except Exception:
        rollback_quietly(connection)
        raise

    return respond(200, {"released": True, "items": released})


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
            segments = path_segments(event)
            if "reserve" in segments:
                return reserve_stock(connection, event)
            if "release" in segments:
                return release_stock(connection, event)
            return respond(404, {"message": "Not found"})
        return respond(405, {"message": "Method not allowed"})
    except KeyError as exc:
        print(f"Missing database setting: {exc}")
        return respond(500, {"message": f"Missing value: {exc}"})
    except Exception as exc:
        print(f"Request failed: {type(exc).__name__}: {exc}")
        return respond(500, {"message": f"{type(exc).__name__}: {exc}"})
