"""Lab 6.2: compare insert throughput with 0 vs 5 secondary indexes."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from connection import get_db
from product_utils import generate_products, insert_batches, create_five_indexes, print_workload

COLLECTION = "lab_6_2_products"

def main():
    client, db = get_db()
    try:
        db.drop_collection(COLLECTION)
        c = db[COLLECTION]
        print(f"Connected | Database: {db.name} | Collection: {COLLECTION}")
        t0 = time.perf_counter()
        insert_batches(c, generate_products(10000, seed=1234, start=0))
        plain = time.perf_counter() - t0
        print(f"Insert 10,000 with only _id index: {plain:.3f} seconds")
        baseline = print_workload(db, c, "Five representative queries, no secondary indexes")
        create_five_indexes(c)
        t1 = time.perf_counter()
        insert_batches(c, generate_products(10000, seed=5678, start=10000))
        indexed = time.perf_counter() - t1
        slowdown = (indexed - plain) / plain * 100 if plain else 0
        print(f"Insert 10,000 with five secondary indexes: {indexed:.3f} seconds")
        print(f"Write-time slowdown: {slowdown:+.2f}% (negative means indexed run was faster)")
        five = print_workload(db, c, "Five representative queries with five indexes (20k docs)")
        for item in list(c.list_indexes()):
            if item["name"] not in ("_id_", "idx_category_price"):
                c.drop_index(item["name"])
        one = print_workload(db, c, "Five representative queries with only critical idx_category_price")
        print("Indexes retained:", [x["name"] for x in c.list_indexes()])
        print("Analysis: More indexes often reduce read cost but add maintenance work to inserts;")
        print("retain indexes for frequent/high-impact queries, and measure under comparable conditions.")
        print("Caution: data volume/cache/order differ between timed phases: repeat trials for rigorous benchmark.")
    finally: client.close()

if __name__ == "__main__": main()
