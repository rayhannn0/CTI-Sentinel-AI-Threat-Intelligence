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
        # Only reset this lab's demo collection; other activity collections are preserved.
        coll = db["lab_5_1_orders"]
        coll.drop()
        coll.insert_many(convert_dates(load_data("orders.json")))
        print("Connected to MongoDB | Database: lab5 | Collection: lab_5_1_orders")
        print("Inserted orders:", coll.count_documents({}))

        monthly = [
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m", "date": "$order_date"}},
                        "revenue": {"$sum": {"$multiply": ["$quantity", "$unit_price"]}},
                        "orders": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        print("\nMONTHLY REVENUE (all statuses):")
        for r in coll.aggregate(monthly):
            print(f"{r['_id']} | Revenue: ${r['revenue']:.2f} | Orders: {r['orders']}")

        top_customers = [
            {"$group": {"_id": "$customer",
                        "total_spent": {"$sum": {"$multiply": ["$quantity", "$unit_price"]}},
                        "products": {"$addToSet": "$product"}}},
            {"$sort": {"total_spent": -1, "_id": 1}},
            {"$limit": 3},
        ]
        print("\nTOP 3 CUSTOMERS:")
        for r in coll.aggregate(top_customers):
            print(f"{r['_id']}: ${r['total_spent']:.2f} | Products: {', '.join(sorted(r['products']))}")

        average_by_status = [
            {"$group": {"_id": "$status",
                        "average_order_value": {"$avg": {"$multiply": ["$quantity", "$unit_price"]}},
                        "orders": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        print("\nAVERAGE ORDER VALUE BY STATUS:")
        for r in coll.aggregate(average_by_status):
            print(f"{r['_id']}: ${r['average_order_value']:.2f} ({r['orders']} orders)")
    finally:
        client.close()

if __name__ == "__main__":
    main()
