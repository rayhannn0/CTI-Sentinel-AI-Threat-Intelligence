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

def bulk_import_idempotent(collection, documents):
    # $set replaces imported fields with the same values on each run.
    # Unique SKU index protects against accidental duplicate identifiers.
    operations = []
    for doc in documents:
        operations.append(UpdateOne({"sku": doc["sku"]}, {"$set": doc}, upsert=True))
    return collection.bulk_write(operations, ordered=True) if operations else None

def main():
    client, collection = get_collection("activity_4_2_import")
    try:
        prepare_collection(collection.database, collection.name)
        collection.create_index("sku", unique=True)
        documents = load_seed(Path(__file__).with_name("products.json"))
        first = bulk_import_idempotent(collection, documents)
        count1 = collection.count_documents({})
        second = bulk_import_idempotent(collection, documents)
        count2 = collection.count_documents({})
        print("First import: upserted", first.upserted_count, "total", count1)
        print("Second import: upserted", second.upserted_count, "modified", second.modified_count, "total", count2)
        assert count1 == count2 == len(documents)
        assert second.upserted_count == 0
        print("PASS: repeated imports create no duplicate SKU records")
    finally:
        client.close()

if __name__ == "__main__":
    main()
