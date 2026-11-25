"""Lab 6.1: generate 50,000 products and explain five queries before/after indexes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from connection import get_db
from product_utils import generate_products, insert_batches, print_workload, create_five_indexes

COLLECTION = "lab_6_1_products"

def prepare(db, force=True):
    if force:
        db.drop_collection(COLLECTION)  # Replaces ONLY this lab's sample collection.
    c = db[COLLECTION]
    if c.count_documents({}) != 50000:
        db.drop_collection(COLLECTION)
        c = db[COLLECTION]
        insert_batches(c, generate_products(50000))
    return c

def main():
    client, db = get_db()
    try:
        print(f"Connected | Database: {db.name} | Collection: {COLLECTION}")
        products = prepare(db)
        print("Generated documents:", products.count_documents({}))
        before = print_workload(db, products, "BEFORE indexes")
        create_five_indexes(products)
        after = print_workload(db, products, "AFTER indexes")
        print("\nImprovement (docs examined):")
        for name in before:
            b = before[name].get("executionStats", {}).get("totalDocsExamined", 0)
            a = after[name].get("executionStats", {}).get("totalDocsExamined", 0)
            print(f"{name}: {b} -> {a}")
        print("Indexes:", [i["name"] for i in products.list_indexes()])
        print("NOTE: $text searches require a text index; this workload uses an explainable prefix-regex name search.")
    finally: client.close()

if __name__ == "__main__": main()
