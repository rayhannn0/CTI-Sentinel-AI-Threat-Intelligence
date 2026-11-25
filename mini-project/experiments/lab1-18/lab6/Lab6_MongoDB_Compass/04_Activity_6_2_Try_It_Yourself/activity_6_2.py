"""Try it yourself 6.2: verify covered query avoids FETCH and document reads."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from connection import get_db
from product_utils import generate_products, insert_batches, explain_find, describe, plan_stages

COLLECTION = "activity_6_2_covered"

def main():
    client, db = get_db()
    try:
        c = db[COLLECTION]
        if c.count_documents({}) < 1000:
            db.drop_collection(COLLECTION)
            c = db[COLLECTION]
            insert_batches(c, generate_products(1000, seed=321))
        c.create_index([("category", 1), ("price", 1)], name="idx_covered_category_price")
        filt = {"category": "Electronics"}
        projection = {"_id": 0, "category": 1, "price": 1}
        sort = [("price", 1)]
        exp = explain_find(db, c, filt, projection, sort, 10)
        print("Covered query:", filt, "projection:", projection)
        print(describe(exp))
        print("First 5 results:", list(c.find(filt, projection).sort(sort).limit(5)))
        stages = plan_stages(exp)
        docs = exp.get("executionStats", {}).get("totalDocsExamined")
        print("FETCH stage eliminated:", "FETCH" not in stages)
        print("totalDocsExamined == 0:", docs == 0)
        if "FETCH" in stages or docs != 0:
            print("WARNING: query was not covered. Inspect explain output and index selection.")
        else:
            print("PASS: Index covers filter, sort, and projection without fetching documents.")
    finally: client.close()

if __name__ == "__main__": main()
