"""BobaBox payment processing service (Lab 9).

Stands in for an independent financial institution: it has its own Lambda
and its own database (payment_service), separate from the storefront's
inventory and order services. The handler name is lambda_handler. Attach it,
with Lambda proxy integration on, to:

  POST /payment

Request body (JSON):

  {
    "cardHolderName": "Jane Doe",
    "creditCardNumber": "4242",   # full number or last 4; only the last 4 are stored
    "expirationDate": "12/27",
    "amount": 47.48
  }

Response: 200 {"paymentToken": "PAY-...", "status": "Approved", "amount": 47.48, "cardLast4": "4242"}

The CVV is never accepted or stored. Set DB_HOST, DB_PORT, DB_NAME, DB_USER,
and DB_PASSWORD on the function, and bundle PyMySQL with the deployment
package (or attach a layer that contains it). Create the table with
database/payment_schema.sql.
"""

import base64
import json
import os
import re
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
UNIQUE_INDEX = "UQ_PAYMENT_TOKEN"

_connection = None


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
        autocommit=True,
    )
    return _connection


def parse_body(event):
    body = event.get("body")
    if event.get("isBase64Encoded") and isinstance(body, str):
        body = base64.b64decode(body).decode("utf-8")
    if body is None or body == "":
        return {}
    if isinstance(body, dict):
        return body
    return json.loads(body)


def new_payment_token():
    return "PAY-" + "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(TOKEN_LENGTH))


def validate(payment):
    holder = str(payment.get("cardHolderName") or "").strip()
    digits = re.sub(r"\D", "", str(payment.get("creditCardNumber") or ""))
    expiration = str(payment.get("expirationDate") or "").strip()

    try:
        amount = round(float(payment.get("amount")), 2)
    except (TypeError, ValueError):
        amount = None

    errors = []
    if len(holder) < 2:
        errors.append("cardHolderName is required")
    if len(digits) < 4:
        errors.append("creditCardNumber must include at least the last 4 digits")
    if not re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", expiration):
        errors.append("expirationDate must be MM/YY")
    if amount is None or amount <= 0:
        errors.append("amount must be a positive number")

    return errors, holder, digits[-4:], expiration, amount


def process_payment(event):
    try:
        payment = parse_body(event)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return respond(400, {"message": "Payment body must be JSON"})

    errors, holder, last4, expiration, amount = validate(payment)
    if errors:
        return respond(400, {"message": "Invalid payment", "errors": errors})

    connection = get_connection()
    with connection.cursor() as cursor:
        for _ in range(TOKEN_ATTEMPTS):
            token = new_payment_token()
            try:
                cursor.execute(
                    """
                    INSERT INTO PAYMENT (PAYMENT_TOKEN, HOLDER_NAME, CARD_LAST4, EXP_DATE, AMOUNT, STATUS)
                    VALUES (%s, %s, %s, %s, %s, 'Approved')
                    """,
                    (token, holder, last4, expiration, amount),
                )
                break
            except pymysql.err.IntegrityError as exc:
                if exc.args[0] == 1062 and UNIQUE_INDEX in str(exc):
                    continue
                raise
        else:
            raise RuntimeError("Could not generate a unique payment token")

    return respond(200, {
        "paymentToken": token,
        "status": "Approved",
        "amount": amount,
        "cardLast4": last4,
    })


def lambda_handler(event, context):
    method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
        or ""
    ).upper()

    if method == "OPTIONS":
        return respond(200, {})
    if method != "POST":
        return respond(405, {"message": "Method not allowed"})
    if pymysql is None:
        return respond(500, {"message": "PyMySQL is not installed on this function"})

    try:
        return process_payment(event)
    except KeyError as exc:
        print(f"Missing database setting: {exc}")
        return respond(500, {"message": f"Missing value: {exc}"})
    except Exception as exc:
        print(f"Payment failed: {type(exc).__name__}: {exc}")
        return respond(500, {"message": f"{type(exc).__name__}: {exc}"})
