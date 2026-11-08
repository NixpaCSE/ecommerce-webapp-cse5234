"""BobaBox shipping processing service (Lab 9).

Stands in for an independent shipping company: it has its own Lambda and its
own database (shipping_service), separate from the storefront's inventory
and order services. The handler name is lambda_handler. It accepts the same
Shipping object from two sources:

  POST /shipping   API Gateway, Lambda proxy integration on
  EventBridge      the orderLambda rule on ShippingBus (source bobabox.order,
                   detail-type OrderReadyForShipping) targets this function,
                   directly or through SNS or SQS

Shipping object (JSON), as the order Lambda publishes it:

  {
    "businessId": "STORE-BOBABOX",
    "orderId": "BBA-7K2M9QXR",
    "street": "1 Main St, Apt 2",
    "city": "Columbus", "state": "OH", "zip": "43210",
    "packets": [
      {"lineItemId": "L1", "weightLb": 2.0},  # one entry per packet
      {"lineItemId": "L2", "weightLb": 3.0}
    ]
  }

Direct API callers may instead nest the address as "address": {"addressLine1",
"addressLine2", "city", "state", "zip"}, use "weight" for weightLb, add
"numberOfPackets" as a check, or send "packetWeights": [2.0, 3.0] in place of
packets (each packet's line item id is then its packet number). Response:
200 {"shippingToken": "SHP-...", "status": "INITIATED", ...}

A business can only ship an order once (UNIQUE business_id, order_id). If the
same order arrives again, for example because EventBridge redelivered the
event, the existing shipment's token is returned and nothing new is stored.

Set DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD on the function, and
bundle PyMySQL with the deployment package. Create the tables with
database/shipping_schema.sql.
"""

import base64
import json
import os
import secrets

try:
    import pymysql
except ImportError:
    pymysql = None

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}

TOKEN_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
TOKEN_LENGTH = 12
TOKEN_ATTEMPTS = 5
ORDER_UNIQUE_INDEX = "UQ_SHIPMENT_BUSINESS_ORDER"
MAX_PACKETS = 100

_connection = None


class InvalidShipment(Exception):
    def __init__(self, errors):
        super().__init__("; ".join(errors))
        self.errors = errors


def respond(status, payload):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps(payload)}


def get_connection():
    global _connection
    if pymysql is None:
        raise RuntimeError("PyMySQL is not installed. Bundle it with the deployment package.")

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
            return str(value).strip()
    return ""


def new_shipping_token():
    return "SHP-" + "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(TOKEN_LENGTH))


def read_packets(shipment):
    """Return [(line_item_id, weight)], or None if the packets are malformed."""
    packets = shipment.get("packets")
    if packets is None and shipment.get("packetWeights") is not None:
        packets = [
            {"lineItemId": str(number), "weight": weight}
            for number, weight in enumerate(shipment["packetWeights"], start=1)
        ]
    if not isinstance(packets, list) or not packets:
        return None

    result = []
    for number, packet in enumerate(packets, start=1):
        if not isinstance(packet, dict):
            return None
        try:
            weight = round(float(packet.get("weight", packet.get("weightLb"))), 2)
        except (TypeError, ValueError):
            return None
        if weight <= 0:
            return None
        result.append((field(packet, "lineItemId", "itemId", "id") or str(number), weight))
    return result


def validate(shipment):
    if not isinstance(shipment, dict):
        raise InvalidShipment(["Shipping object must be a JSON object"])

    errors = []
    business_id = field(shipment, "businessId", "businessID")
    order_id = field(shipment, "orderId", "orderReference", "confirmationNumber")
    if not business_id:
        errors.append("businessId is required")
    if not order_id:
        errors.append("orderId is required")

    # The order Lambda sends street/city/state/zip at the top level. Direct
    # API callers may nest them under "address" instead.
    address = shipment.get("address") or shipment.get("shippingAddress") or shipment
    if not isinstance(address, dict):
        address = {}
    if not field(address, "addressLine1", "street"):
        errors.append("street (or address.addressLine1) is required")
    for name in ("city", "state", "zip"):
        if not field(address, name, "postalCode" if name == "zip" else name):
            errors.append(f"{name} is required")

    packets = read_packets(shipment)
    if packets is None:
        errors.append("packets must be a list of {lineItemId, weight} with positive weights (lb)")
    elif len(packets) > MAX_PACKETS:
        errors.append(f"A shipment can have at most {MAX_PACKETS} packets")
    elif shipment.get("numberOfPackets") is not None:
        try:
            count = int(shipment["numberOfPackets"])
        except (TypeError, ValueError):
            count = None
        if count != len(packets):
            errors.append("numberOfPackets must match the number of packets")

    if errors:
        raise InvalidShipment(errors)

    street = field(address, "addressLine1", "street")
    line2 = field(address, "addressLine2")
    return {
        "business_id": business_id,
        "order_id": order_id,
        "street": f"{street}, {line2}" if line2 else street,
        "city": field(address, "city"),
        "state": field(address, "state"),
        "zip": field(address, "zip", "postalCode"),
        "packets": packets,
    }


def existing_shipment(connection, business_id, order_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.shipping_token, s.status, COUNT(p.packet_id) AS packets,
                   COALESCE(SUM(p.weight_lb), 0) AS weight
            FROM shipment s
            LEFT JOIN packet p ON p.shipping_token = s.shipping_token
            WHERE s.business_id = %s AND s.order_id = %s
            GROUP BY s.shipping_token, s.status
            """,
            (business_id, order_id),
        )
        return cursor.fetchone()


def create_shipment(shipment):
    data = validate(shipment)
    packets = data["packets"]
    summary = {
        "orderId": data["order_id"],
        "numberOfPackets": len(packets),
        "totalWeight": round(sum(weight for _, weight in packets), 2),
    }

    connection = get_connection()
    connection.begin()
    try:
        with connection.cursor() as cursor:
            token = None
            for _ in range(TOKEN_ATTEMPTS):
                candidate = new_shipping_token()
                try:
                    cursor.execute(
                        """
                        INSERT INTO shipment
                            (shipping_token, business_id, order_id, street, city, state, zip)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            candidate,
                            data["business_id"],
                            data["order_id"],
                            data["street"],
                            data["city"],
                            data["state"],
                            data["zip"],
                        ),
                    )
                    token = candidate
                    break
                except pymysql.err.IntegrityError as exc:
                    if exc.args[0] != 1062:
                        raise
                    if ORDER_UNIQUE_INDEX in str(exc):
                        rollback_quietly(connection)
                        row = existing_shipment(connection, data["business_id"], data["order_id"])
                        rollback_quietly(connection)
                        return {
                            **summary,
                            "shippingToken": row["shipping_token"],
                            "status": row["status"],
                            "numberOfPackets": int(row["packets"]),
                            "totalWeight": float(row["weight"]),
                            "duplicate": True,
                        }
                    # Otherwise the random token collided with an existing one.
            if token is None:
                raise RuntimeError("Could not generate a unique shipping token")

            cursor.executemany(
                """
                INSERT INTO packet (shipping_token, packet_id, line_item_id, weight_lb)
                VALUES (%s, %s, %s, %s)
                """,
                [
                    (token, number, line_item_id, weight)
                    for number, (line_item_id, weight) in enumerate(packets, start=1)
                ],
            )
        connection.commit()
    except Exception:
        rollback_quietly(connection)
        raise

    return {**summary, "shippingToken": token, "status": "INITIATED"}


def shipments_from_records(event):
    """Yield the Shipping object from each record an event source delivers.

    EventBridge targets the function with a single event whose "detail" is the
    Shipping object. SNS and SQS wrap that same EventBridge event in Records.
    """
    if "detail" in event:
        yield event["detail"]
        return

    for record in event.get("Records") or []:
        if "Sns" in record:
            message = json.loads(record["Sns"]["Message"])
        else:
            message = json.loads(record.get("body") or "{}")
        yield message.get("detail", message)


def handle_records(event):
    results = []
    for shipment in shipments_from_records(event):
        try:
            result = create_shipment(shipment)
            print(f"Shipment initiated: {json.dumps(result)}")
            results.append(result)
        except InvalidShipment as exc:
            # Retrying will not fix bad input, so log it instead of raising.
            print(f"Rejected shipment {json.dumps(shipment)}: {exc}")
            results.append({"status": "REJECTED", "errors": exc.errors})
    return {"shipments": results}


def handle_api(event, method):
    if method == "OPTIONS":
        return respond(200, {})
    if method != "POST":
        return respond(405, {"message": "Method not allowed"})

    try:
        shipment = parse_body(event)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return respond(400, {"message": "Shipping body must be JSON"})

    try:
        return respond(200, create_shipment(shipment))
    except InvalidShipment as exc:
        return respond(400, {"message": "Invalid shipment", "errors": exc.errors})


def lambda_handler(event, context):
    method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
        or ""
    ).upper()

    if method:
        if pymysql is None:
            return respond(500, {"message": "PyMySQL is not installed on this function"})
        try:
            return handle_api(event, method)
        except KeyError as exc:
            print(f"Missing database setting: {exc}")
            return respond(500, {"message": f"Missing value: {exc}"})
        except Exception as exc:
            print(f"Shipping failed: {type(exc).__name__}: {exc}")
            return respond(500, {"message": f"{type(exc).__name__}: {exc}"})

    # Not an API Gateway request, so it came from EventBridge, SNS, or SQS.
    # Errors are raised so the source can retry delivery.
    return handle_records(event)
