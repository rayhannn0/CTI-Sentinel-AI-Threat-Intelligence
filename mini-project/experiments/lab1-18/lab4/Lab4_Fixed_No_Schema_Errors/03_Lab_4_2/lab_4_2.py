from pathlib import Path
import json
# Import the one shared connection from the main Lab4 folder.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from connection import get_collection
PRODUCT_VALIDATOR = {"$jsonSchema": {"bsonType": "object", "required": ["sku", "name", "price", "stock", "tags"], "properties": {
    "sku": {"bsonType": "string"}, "name": {"bsonType": "string"},
    "price": {"bsonType": ["int", "long", "double", "decimal"], "minimum": 0.01},
    "stock": {"bsonType": ["int", "long"], "minimum": 0},
    "tags": {"bsonType": "array", "items": {"bsonType": "string"}},
    "is_active": {"bsonType": "bool"}
}}}
def prepare_collection(db, collection_name, reset=True):
    if reset:
        db.drop_collection(collection_name)  # Only resets this activity's demo collection.
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name, validator=PRODUCT_VALIDATOR)
    return db[collection_name]
def load_seed(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

from pymongo import UpdateOne

def upsert_product(collection, sku, price):
    if price <= 0:
        raise ValueError("price must be positive")
    return collection.update_one(
        {"sku": sku},
        {"$set": {"price": price},
         "$setOnInsert": {"sku": sku, "name": f"New Product {sku}", "stock": 0, "tags": [], "is_active": True}},
        upsert=True)

def main():
    client, collection = get_collection("lab_4_2_products")
    try:
        prepare_collection(collection.database, collection.name)
        collection.create_index("sku", unique=True)
        collection.insert_many(load_seed(Path(__file__).with_name("products.json")))
        updated = upsert_product(collection, "A", 34.99)
        inserted = upsert_product(collection, "K", 59.99)
        print("Existing SKU A matched:", updated.matched_count, "upserted:", updated.upserted_id is not None)
        print("New SKU K upserted:", inserted.upserted_id is not None)
        operations = [UpdateOne({"sku":sku},{"$inc":{"stock":10}}) for sku in ("A","B","C")]
        operations += [UpdateOne({"sku":sku},{"$set":{"is_active":False}}) for sku in ("D","E")]
        result = collection.bulk_write(operations, ordered=True)
        print("Bulk matched:", result.matched_count)
        print("Bulk modified:", result.modified_count)
        print("Bulk upserted:", result.upserted_count)
        for sku in "ABCDE":
            row = collection.find_one({"sku": sku}, {"_id": 0, "sku":1, "stock":1, "is_active":1})
            print(row)
    finally:
        client.close()

if __name__ == "__main__":
    main()
