from pathlib import Path
import sys
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from connection import get_database


def load_data(filename):
    return json.loads((Path(__file__).resolve().parent / filename).read_text(encoding="utf-8"))


def convert_dates(rows):
    for row in rows:
        row["order_date"] = datetime.fromisoformat(row["order_date"])
    return rows

def main():
    client, db = get_database()
    try:
        products, orders = db["lab_5_2_products"], db["lab_5_2_orders"]
        products.drop()
        orders.drop()
        data = load_data("data.json")
        products.insert_many(data["products"])
        orders.insert_many(convert_dates(data["orders"]))
        orders.create_index("product_id")
        print("Connected to MongoDB | Database: lab5")
        print(f"Collections: lab_5_2_products ({products.count_documents({})}), "
              f"lab_5_2_orders ({orders.count_documents({})})")
        join_pipeline = [
            {"$lookup": {"from": "lab_5_2_products", "localField": "product_id",
                         "foreignField": "_id", "as": "product"}},
            {"$unwind": "$product"},
            {"$project": {"_id": 0, "order_id": 1,
                          "order_date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$order_date"}},
                          "product_name": "$product.name", "quantity": 1,
                          "total": {"$multiply": ["$quantity", "$product.base_price"]}}},
            {"$sort": {"order_id": 1}}
        ]
        print("\nORDER + PRODUCT JOIN:")
        for r in orders.aggregate(join_pipeline):
            print(f"{r['order_id']} | {r['order_date']} | {r['product_name']} | "
                  f"Qty: {r['quantity']} | Total: ${r['total']:.2f}")
        never_ordered_pipeline = [
            {"$lookup": {"from": "lab_5_2_orders", "localField": "_id", "foreignField": "product_id",
                         "as": "matching_orders"}},
            {"$match": {"matching_orders": {"$eq": []}}},
            {"$project": {"_id": 0, "name": 1, "category": 1}},
            {"$sort": {"name": 1}}
        ]
        print("\nPRODUCTS NEVER ORDERED:")
        for r in products.aggregate(never_ordered_pipeline):
            print(f"{r['name']} ({r['category']})")
    finally:
        client.close()

if __name__ == "__main__":
    main()
