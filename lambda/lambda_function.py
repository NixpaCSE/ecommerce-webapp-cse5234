"""BobaBox inventory and order Lambda.

Paste this file into the AWS Lambda console (Python 3.12). The handler name
is lambda_handler. Attach this same function, with Lambda proxy integration
on, to:

  GET  /inventory-management/inventory
  GET  /inventory-management/inventory/items/{id}
  GET  /inventory-management/inventory/items        (?name=)
  POST /order-processing/order

Reads and writes the storefront RDS MySQL database. Set DB_HOST, DB_PORT,
DB_NAME, DB_USER, and DB_PASSWORD on the function. PyMySQL is not part of
the Lambda runtime; attach a layer that contains it before testing.

Card data is not written here. After stock is reserved, place_order POSTs
the card to the payment Lambda at PAYMENT_API_URL and stores only the
token that service returns on CUSTOMER_ORDER.PAYMENT_TOKEN.

After that order is committed, place_order puts an OrderReadyForShipping
event on a custom EventBridge bus and returns. It does not wait for
shipping, and it does not call SHIPPING_API_URL. That URL is only for a
direct POST /shipping. A rule on the custom bus invokes the shipping
Lambda. An optional second target on the same rule is an SNS topic for
email or SMS. The bus name is ShippingBus. Set EVENT_BUS_NAME only to
override it. This function's role needs events:PutEvents on that bus.
BUSINESS_ID defaults to STORE-BOBABOX.
Each line item is one packet, weight = quantity * PACKET_UNIT_WEIGHT_LB
(default 1.0, so 10 units is 10.00 lb).

ITEM is matched on its primary key. The confirmation number returned to the
client is BBA- plus CUSTOMER_ORDER.CONFIRMATION_CODE, a random code that the
database guarantees is unique through a UNIQUE constraint.

ITEM.IMAGE_URL holds the public S3 URL for each kit photo. ITEM has no
gradient column, so that response field is an empty string.
"""

import base64
import json
import os
import secrets
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

try:
    import boto3
except ImportError:  # Present in the Lambda runtime. Missing in the console editor.
    boto3 = None

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

# No 0/O/1/I/L, so codes are easy to read aloud or type from an email.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
CODE_ATTEMPTS = 5
UNIQUE_INDEX = "UQ_CUSTOMER_ORDER_CONFIRMATION_CODE"

# BobaBox's registration id with the shipping company. Sent on every
# shipment event and stored on the shipment row. There is no business table.
DEFAULT_BUSINESS_ID = "STORE-BOBABOX"
# Pounds per unit. 10 units of one line item become one packet of 10.00 lb.
UNIT_WEIGHT_LB = 1.0
SHIPPING_EVENT_SOURCE = "bobabox.order"
SHIPPING_EVENT_DETAIL_TYPE = "OrderReadyForShipping"
DEFAULT_EVENT_BUS_NAME = "ShippingBus"

_connection = None


class PaymentError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def new_confirmation_code():
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


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


def request_payment(payment, amount):
    """Ask the payment service to store the card and return its token.

    PAYMENT_API_URL is the full POST /payments/payment URL. The payment
    Lambda requires amount and returns paymentToken. This function never
    writes the card number to the storefront database.
    """
    url = os.environ["PAYMENT_API_URL"]
    payload = json.dumps({
        "cardHolderName": field(payment, "cardHolderName", "holderName"),
        "creditCardNumber": field(payment, "creditCardNumber", "cardNumber"),
        "expirationDate": field(payment, "expirationDate", "expDate"),
        "amount": amount,
    }).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def call():
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
                message = parsed.get("message") or raw
                errors = parsed.get("errors")
                if errors:
                    message = f"{message}: {', '.join(errors)}"
            except json.JSONDecodeError:
                message = raw or str(exc.reason)
            raise PaymentError(exc.code, message or "Payment request failed") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise PaymentError(502, f"Payment service unavailable: {exc}") from exc

    # A black-holed DNS lookup ignores the socket timeout and would run
    # until Lambda is killed. API Gateway then shows "Internal server error".
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            body = pool.submit(call).result(timeout=8)
    except FuturesTimeout as exc:
        raise PaymentError(502, "Payment service timed out") from exc

    token = None
    if isinstance(body, dict):
        token = body.get("paymentToken") or body.get("token")
    if not token:
        raise PaymentError(502, "Payment service did not return a token")
    return str(token)


def shipment_street(shipping):
    line1 = field(shipping, "addressLine1", "address1").strip()
    line2 = field(shipping, "addressLine2", "address2").strip()
    if line1 and line2:
        return f"{line1}, {line2}"
    return line1 or line2


def custom_event_bus():
    """Publish to ShippingBus. EVENT_BUS_NAME overrides that name."""
    name = (os.environ.get("EVENT_BUS_NAME") or DEFAULT_EVENT_BUS_NAME).strip()
    if not name or name.lower() == "default":
        raise RuntimeError(
            "EVENT_BUS_NAME must be the custom bus ShippingBus. "
            "This function does not call SHIPPING_API_URL."
        )
    return name


def publish_shipping_request(shipping, order_id, lines):
    """Hand the order to EventBridge after it is saved. Do not wait.

    PutEvents returns when the bus accepts the event. The shipping Lambda
    runs later, from the rule, and this function never calls it or
    SHIPPING_API_URL. One line item is one packet, however large its
    quantity is.
    """
    if boto3 is None:
        raise RuntimeError("boto3 is not available")

    bus = custom_event_bus()
    try:
        unit_weight = float(os.environ.get("PACKET_UNIT_WEIGHT_LB", str(UNIT_WEIGHT_LB)))
    except ValueError:
        unit_weight = UNIT_WEIGHT_LB

    packets = []
    for index, line in enumerate(lines, start=1):
        packets.append({
            "lineItemId": f"L{index}",
            "weightLb": round(line["quantity"] * unit_weight, 2),
        })

    detail = {
        "businessId": os.environ.get("BUSINESS_ID") or DEFAULT_BUSINESS_ID,
        "orderId": order_id,
        "street": shipment_street(shipping),
        "city": field(shipping, "city"),
        "state": field(shipping, "state"),
        "zip": field(shipping, "zip", "postalCode", "postal_code"),
        "packets": packets,
    }
    result = boto3.client("events").put_events(Entries=[{
        "Source": SHIPPING_EVENT_SOURCE,
        "DetailType": SHIPPING_EVENT_DETAIL_TYPE,
        "EventBusName": bus,
        "Detail": json.dumps(detail),
    }])
    failed = result.get("FailedEntryCount") or 0
    entry = (result.get("Entries") or [{}])[0]
    if failed:
        message = entry.get("ErrorMessage") or entry.get("ErrorCode") or "PutEvents failed"
        raise RuntimeError(message)
    print(f"OrderReadyForShipping accepted on {bus} for {order_id}: {entry.get('EventId')}")


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

    # Price the cart before payment. Roll the read back before the HTTP
    # call so a slow payment service cannot hold locks on ITEM.
    try:
        priced = []
        total = 0.0
        with connection.cursor() as cursor:
            for item_id, quantity in requested.items():
                cursor.execute(
                    """
                    SELECT ID, ITEM_NUMBER, NAME, UNIT_PRICE, AVAILABLE_QUANTITY
                    FROM ITEM
                    WHERE ID = %s
                    """,
                    (item_id,),
                )
                item = cursor.fetchone()
                if item is None:
                    return respond(404, {"message": "Item not found", "itemId": str(item_id)})

                available = int(item["AVAILABLE_QUANTITY"] or 0)
                if quantity > available:
                    return respond(409, {
                        "message": "Insufficient quantity",
                        "itemId": str(item["ID"]),
                        "name": item["NAME"],
                        "requested": quantity,
                        "available": available,
                    })

                price = float(item["UNIT_PRICE"] or 0)
                priced.append({
                    "id": item["ID"],
                    "name": item["NAME"] or "",
                    "price": price,
                    "quantity": quantity,
                    "item_number": item["ITEM_NUMBER"] if item["ITEM_NUMBER"] is not None else item["ID"],
                })
                total = round(total + price * quantity, 2)
    finally:
        rollback_quietly(connection)

    try:
        payment_token = request_payment(payment, total)
    except PaymentError as exc:
        return respond(exc.status, {"message": str(exc)})

    connection.begin()
    try:
        with connection.cursor() as cursor:
            ordered = []
            for line in priced:
                item_id = line["id"]
                quantity = line["quantity"]
                cursor.execute(
                    """
                    SELECT ID, NAME, AVAILABLE_QUANTITY
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

                ordered.append({
                    "id": str(line["id"]),
                    "name": line["name"],
                    "price": line["price"],
                    "quantity": quantity,
                    "item_number": line["item_number"],
                })

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

            # The UNIQUE constraint on CONFIRMATION_CODE is what guarantees
            # uniqueness. If a random code ever collides, MySQL rejects only
            # this INSERT (the rest of the transaction stays intact) and we
            # try a fresh code.
            order_id = None
            confirmation_code = None
            for _ in range(CODE_ATTEMPTS):
                confirmation_code = new_confirmation_code()
                try:
                    cursor.execute(
                        """
                        INSERT INTO CUSTOMER_ORDER
                            (CUSTOMER_NAME, CUSTOMER_EMAIL, SHIPPING_INFO_ID_FK,
                             PAYMENT_TOKEN, STATUS, CONFIRMATION_CODE)
                        VALUES (%s, %s, %s, %s, 'New', %s)
                        """,
                        (
                            field(shipping, "name", "customerName"),
                            field(shipping, "email"),
                            shipping_id,
                            payment_token,
                            confirmation_code,
                        ),
                    )
                    order_id = cursor.lastrowid
                    break
                except pymysql.err.IntegrityError as exc:
                    # 1062 = duplicate key. Only retry if it was our code.
                    if exc.args[0] == 1062 and UNIQUE_INDEX in str(exc):
                        continue
                    raise

            if order_id is None:
                raise RuntimeError("Could not generate a unique confirmation code")

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
    except PaymentError as exc:
        rollback_quietly(connection)
        return respond(exc.status, {"message": str(exc)})
    except Exception:
        rollback_quietly(connection)
        raise

    # Validate, pay, and commit are already done. Publishing is the async
    # step: EventBridge accepts the event and this request returns without
    # a shipping token. A publish failure must not fail checkout, or the
    # customer will retry and place a second order.
    confirmation_number = f"BBA-{confirmation_code}"
    shipping_status = "queued"
    shipping_error = ""
    try:
        publish_shipping_request(shipping, confirmation_number, ordered)
    except Exception as exc:
        shipping_status = "not queued"
        shipping_error = str(exc)
        print(f"Shipping event was not published: {type(exc).__name__}: {exc}")

    card = field(payment, "creditCardNumber", "cardNumber")
    body = {
        "confirmationNumber": confirmation_number,
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
        "shippingStatus": shipping_status,
        "cardLast4": card[-4:] if card else "",
    }
    if shipping_error:
        body["shippingError"] = shipping_error
    return respond(200, body)


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