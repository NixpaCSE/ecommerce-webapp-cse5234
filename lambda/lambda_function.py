"""BobaBox inventory and order Lambda.

Paste this file into the AWS Lambda console (Python 3.12). The handler name
is lambda_handler. Attach this same function, with Lambda proxy integration
on, to:

  GET  /inventory-management/inventory
  GET  /inventory-management/inventory/items/{id}
  GET  /inventory-management/inventory/items        (?name=)
  POST /order-processing/order

Each kit has STOCK units. An order line above that quantity is rejected.
"""

import json
import uuid

STOCK = 50

INVENTORY = [
    {
        "id": "1",
        "name": "Strawberry Milk Tea Kit",
        "image": "/images/strawberry.jpg",
        "description": "Real strawberry purée, black tea, and tapioca pearls. Makes 6 drinks.",
        "price": 22.49,
        "quantity": STOCK,
        "gradient": "radial-gradient(circle at 30% 25%, #fff0f5 0%, #ff7aa8 25%, #ff1f6b 55%, #b0003a 85%, #5c0020 100%)",
    },
    {
        "id": "2",
        "name": "Taro Milk Tea Kit",
        "image": "/images/taro.jpg",
        "description": "Real taro powder, jasmine tea, and tapioca pearls. Makes 6 drinks.",
        "price": 23.99,
        "quantity": STOCK,
        "gradient": "linear-gradient(135deg, #12043a 5%, #5b2bd6 38%, #e6d4ff 50%, #7c4dff 60%, #1e0b4f 95%)",
    },
    {
        "id": "3",
        "name": "Brown Sugar Boba Kit",
        "image": "/images/brown-sugar.jpg",
        "description": "Slow-cooked brown sugar syrup and tapioca pearls. Just add milk. Makes 6 drinks.",
        "price": 24.99,
        "quantity": STOCK,
        "gradient": "radial-gradient(circle at 30% 25%, rgba(255, 255, 255, 0.55), transparent 40%), linear-gradient(155deg, #fff1dc 0%, #f7d9b0 18%, #7a3b10 30%, #f0c48c 42%, #4a2108 55%, #e2a868 68%, #2b1407 85%)",
    },
    {
        "id": "4",
        "name": "Matcha Latte Kit",
        "image": "/images/matcha.jpg",
        "description": "Ceremonial-grade matcha, cane syrup, and tapioca pearls. Makes 6 drinks.",
        "price": 26.99,
        "quantity": STOCK,
        "gradient": "radial-gradient(circle at 35% 30%, #f4ff9e 0%, #c6f04d 30%, #6fa82a 65%, #1f3d10 100%)",
    },
    {
        "id": "5",
        "name": "Mango Green Tea Kit",
        "image": "/images/mango.jpg",
        "description": "Jasmine green tea, mango syrup, and popping boba. Makes 6 drinks.",
        "price": 22.99,
        "quantity": STOCK,
        "gradient": "radial-gradient(circle at 30% 30%, #fff59d 0%, #ffc107 25%, #ff7a1a 50%, #e53935 75%, #7a1010 100%)",
    },
]

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def respond(status, payload):
    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": json.dumps(payload),
    }


def find_item(item_id):
    for item in INVENTORY:
        if item["id"] == str(item_id):
            return item
    return None


def get_inventory(event):
    path_params = event.get("pathParameters") or {}
    query = event.get("queryStringParameters") or {}
    item_id = path_params.get("id")
    name = query.get("name")

    if item_id:
        item = find_item(item_id)
        if item is None:
            return respond(404, {"message": "Item not found"})
        return respond(200, item)

    if name:
        needle = name.lower()
        matches = [item for item in INVENTORY if needle in item["name"].lower()]
        return respond(200, matches)

    return respond(200, INVENTORY)


def place_order(event):
    try:
        order = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
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
        item_id = str(line.get("id", ""))
        try:
            quantity = int(line.get("quantity", 0))
        except (TypeError, ValueError):
            return respond(400, {"message": f"Invalid quantity for item {item_id}"})
        if quantity <= 0:
            return respond(400, {"message": f"Quantity for item {item_id} must be at least 1"})
        requested[item_id] = requested.get(item_id, 0) + quantity

    ordered = []
    total = 0
    for item_id, quantity in requested.items():
        item = find_item(item_id)
        if item is None:
            return respond(404, {"message": "Item not found", "itemId": item_id})
        if quantity > item["quantity"]:
            return respond(409, {
                "message": "Insufficient quantity",
                "itemId": item["id"],
                "name": item["name"],
                "requested": quantity,
                "available": item["quantity"],
            })
        ordered.append({
            "id": item["id"],
            "name": item["name"],
            "price": item["price"],
            "quantity": quantity,
        })
        total += item["price"] * quantity

    # Demo-only: Lambda memory is not durable or shared across instances.
    for item_id, quantity in requested.items():
        find_item(item_id)["quantity"] -= quantity

    card = str(payment.get("creditCardNumber") or "")
    return respond(200, {
        "confirmationNumber": "BBA-" + uuid.uuid4().hex[:8].upper(),
        "items": ordered,
        "total": round(total, 2),
        "shipping": shipping,
        "cardLast4": card[-4:] if card else "",
    })


def lambda_handler(event, context):
    method = (event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method") or "").upper()

    if method == "OPTIONS":
        return respond(200, {})
    if method == "GET":
        return get_inventory(event)
    if method == "POST":
        return place_order(event)

    return respond(405, {"message": "Method not allowed"})
