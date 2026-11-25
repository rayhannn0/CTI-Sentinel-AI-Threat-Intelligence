"""Try it yourself 6.1: run five queries repeatedly and inspect $indexStats."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from connection import get_db
from product_utils import generate_products, insert_batches, create_five_indexes, workload

COLLECTION = "activity_6_1_index_usage"

def main():
    client, db = get_db()
    try:
        c = db[COLLECTION]
        if c.count_documents({}) != 50000:
            db.drop_collection(COLLECTION)
            c = db[COLLECTION]
            insert_batches(c, generate_products(50000))
        create_five_indexes(c)
        # Keep indexes and collection intact on repeat runs to see usage accumulate.
        for _ in range(12):
            for _, filt, projection, sort, limit in workload():
                cur = c.find(filt, projection).limit(limit)
                if sort: cur = cur.sort(sort)
                list(cur)
        stats = list(c.aggregate([{"$indexStats": {}}, {"$project": {"name": 1, "accesses.ops": 1}}, {"$sort": {"accesses.ops": -1}}]))
        print("Index usage (ops since MongoDB server/index creation):")
        for row in stats:
            print(f"{row['name']}: {row.get('accesses', {}).get('ops', 0)} ops")
        print("Most frequently used:", stats[0]["name"] if stats else "none")
        print("Note: indexStats includes other operations; counts reset when indexes/server restart.")
    finally: client.close()

if __name__ == "__main__": main()
