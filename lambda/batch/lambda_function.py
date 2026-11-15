"""BobaBox inventory batch Lambda.

Paste this file into its own AWS Lambda function (Python 3.12). The handler
name is lambda_handler. An EventBridge Scheduler schedule invokes it every
15 minutes (rate(15 minutes)). It has no API Gateway route, and it ignores
the event payload.

Each run, in one transaction on the storefront database:
  1. Lock every ITEM row, in ID order.
  2. Read CUSTOMER_ORDER rows with STATUS 'New' and sum their line items.
  3. Subtract those quantities from ITEM.AVAILABLE_QUANTITY.
  4. Set those orders to STATUS 'Processed'.

The order Lambda locks ITEM rows (in ID order) before it inserts an order,
so while this function holds every ITEM lock no order can be half-saved.
Every 'New' order it reads is complete, and no new one can commit until
this run finishes. Two overlapping runs also queue on the same locks, so an
order is never subtracted twice.

Set DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD for the storefront
database. PyMySQL is not part of the Lambda runtime; attach a layer or zip
that contains it. Run it in the same VPC, subnets, and security groups as
the order Lambda. A 30 second timeout is plenty.
"""

import os

try:
    import pymysql
except ImportError:  # The console editor cannot bundle this package.
    pymysql = None

_connection = None


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
        read_timeout=20,
        write_timeout=20,
        autocommit=False,
    )
    return _connection


def process_new_orders(connection):
    connection.begin()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ID, ITEM_NUMBER, NAME
                FROM ITEM
                ORDER BY ID
                FOR UPDATE
                """
            )
            # The order Lambda stores ITEM_NUMBER on each line item, or the
            # ITEM ID when ITEM_NUMBER is empty.
            items_by_number = {}
            for item in cursor.fetchall():
                key = item["ITEM_NUMBER"] if item["ITEM_NUMBER"] is not None else item["ID"]
                items_by_number[key] = item

            cursor.execute(
                """
                SELECT ID
                FROM CUSTOMER_ORDER
                WHERE STATUS = 'New'
                ORDER BY ID
                """
            )
            order_ids = [row["ID"] for row in cursor.fetchall()]
            if not order_ids:
                connection.commit()
                return {"processedOrders": 0, "orderIds": [], "itemsUpdated": []}

            placeholders = ", ".join(["%s"] * len(order_ids))
            cursor.execute(
                f"""
                SELECT ITEM_NUMBER, SUM(QUANTITY) AS TOTAL
                FROM CUSTOMER_ORDER_LINE_ITEM
                WHERE CUSTOMER_ORDER_ID_FK IN ({placeholders})
                GROUP BY ITEM_NUMBER
                """,
                order_ids,
            )
            totals = cursor.fetchall()

            items_updated = []
            for row in totals:
                quantity = int(row["TOTAL"] or 0)
                item = items_by_number.get(row["ITEM_NUMBER"])
                if item is None:
                    print(f"Skipping {quantity} units of unknown item number {row['ITEM_NUMBER']}")
                    continue
                cursor.execute(
                    """
                    UPDATE ITEM
                    SET AVAILABLE_QUANTITY = AVAILABLE_QUANTITY - %s
                    WHERE ID = %s
                    """,
                    (quantity, item["ID"]),
                )
                items_updated.append({"itemId": item["ID"], "name": item["NAME"], "subtracted": quantity})

            cursor.execute(
                f"""
                UPDATE CUSTOMER_ORDER
                SET STATUS = 'Processed'
                WHERE ID IN ({placeholders}) AND STATUS = 'New'
                """,
                order_ids,
            )

        connection.commit()
    except Exception:
        try:
            connection.rollback()
        except pymysql.MySQLError:
            pass
        raise

    return {"processedOrders": len(order_ids), "orderIds": order_ids, "itemsUpdated": items_updated}


def lambda_handler(event, context):
    result = process_new_orders(get_connection())
    print(
        f"Batch processed {result['processedOrders']} order(s) {result['orderIds']}; "
        f"inventory changes: {result['itemsUpdated']}"
    )
    return result
