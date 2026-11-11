"""BobaBox inventory Lambda.

Paste this file into its own AWS Lambda function (Python 3.12). The handler
name is lambda_handler. Attach this function, with Lambda proxy integration
on, to the existing catalog routes only:

  GET  /inventory-management/inventory
  GET  /inventory-management/inventory/items/{id}
  GET  /inventory-management/inventory/items        (?name=)

The order Lambda is a separate function. It updates ITEM itself when a
customer checks out. This function only reads the catalog.

Set DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD. PyMySQL is not part
of the Lambda runtime; attach a layer that contains it.

ITEM.IMAGE_URL holds the public S3 URL for each kit photo. ITEM has no
gradient column, so that response field is an empty string.
"""

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
    "Access-Control-Allow-Methods": "GET,OPTIONS",
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
        # so the next request does not reuse this snapshot.
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

    if method != "GET":
        return respond(405, {"message": "Method not allowed"})

    try:
        connection = get_connection()
        rollback_quietly(connection)
        return get_inventory(connection, event)
    except KeyError as exc:
        print(f"Missing database setting: {exc}")
        return respond(500, {"message": f"Missing value: {exc}"})
    except Exception as exc:
        print(f"Request failed: {type(exc).__name__}: {exc}")
        return respond(500, {"message": f"{type(exc).__name__}: {exc}"})
