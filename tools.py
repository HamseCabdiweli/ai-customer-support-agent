import json
from pathlib import Path


def get_order(order_id):
    with Path(__file__).with_name("orders.json").open() as file:
        orders = json.load(file)

    for order in orders:
        if order["order_id"] == str(order_id).strip():
            return order
    return None
