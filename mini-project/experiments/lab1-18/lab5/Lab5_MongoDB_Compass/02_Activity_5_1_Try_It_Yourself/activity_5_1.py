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
        coll = db["activity_5_1_buckets"]
        coll.drop()
        coll.insert_many(convert_dates(load_data("orders.json")))
        print("Connected to MongoDB | Database: lab5 | Collection: activity_5_1_buckets")
        # $bucket ranges are lower-inclusive, upper-exclusive.
        # With integer USD examples, 201+ is LARGE; 200 is MEDIUM.
        pipeline = [
            {"$project": {"order_id": 1, "total": {"$multiply": ["$quantity", "$unit_price"]}}},
            {"$bucket": {
                "groupBy": "$total",
                "boundaries": [0, 50, 201, 1000000000],
                "default": "Outside range",
                "output": {"order_count": {"$sum": 1}, "order_ids": {"$push": "$order_id"},
                           "total_value": {"$sum": "$total"}}
            }}
        ]
        labels = {0: "Small (under $50)", 50: "Medium ($50-$200)", 201: "Large (over $200)"}
        print("\nORDER BUCKETS:")
        for r in coll.aggregate(pipeline):
            print(f"{labels.get(r['_id'],r['_id'])}: {r['order_count']} orders | "
                  f"Combined value: ${r['total_value']:.2f} | IDs: {', '.join(r['order_ids'])}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
