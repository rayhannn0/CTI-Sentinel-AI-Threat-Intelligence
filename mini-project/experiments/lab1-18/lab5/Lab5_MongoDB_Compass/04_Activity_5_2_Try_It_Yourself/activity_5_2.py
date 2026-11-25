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
        products, orders = db["activity_5_2_products"], db["activity_5_2_orders"]
        products.drop()
        orders.drop()
        data = load_data("data.json")
        products.insert_many(data["products"])
        orders.insert_many(convert_dates(data["orders"]))
        orders.create_index("product_id")
        print("Connected to MongoDB | Database: lab5")
        print("Collections: activity_5_2_products, activity_5_2_orders")
        # Pipeline form of $lookup filters FOREIGN products before joining.
        # Only electronics products costing at least $50 pass the sub-pipeline.
        pipeline = [
            {"$lookup": {
                "from": "activity_5_2_products",
                "let": {"ordered_product_id": "$product_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$and": [
                        {"$eq": ["$_id", "$$ordered_product_id"]},
                        {"$eq": ["$category", "electronics"]},
                        {"$gte": ["$base_price", 50]}
                    ]}}},
                    {"$project": {"_id": 0, "name": 1, "base_price": 1, "category": 1}}
                ],
                "as": "matched_product"
            }},
            {"$unwind": "$matched_product"},
            {"$project": {"_id": 0, "order_id": 1,
                          "product": "$matched_product.name", "quantity": 1,
                          "total": {"$multiply": ["$quantity", "$matched_product.base_price"]}}},
            {"$sort": {"order_id": 1}}
        ]
        print("\nPIPELINE $lookup: electronics products with base_price >= $50")
        matches = list(orders.aggregate(pipeline))
        for r in matches:
            print(f"{r['order_id']} | {r['product']} | Qty: {r['quantity']} | Total: ${r['total']:.2f}")
        print("Matching orders:", len(matches))
    finally:
        client.close()

if __name__ == "__main__":
    main()
