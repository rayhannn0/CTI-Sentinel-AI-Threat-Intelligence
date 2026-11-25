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

import re

def search_products(collection, search_string):
    # Escape regex metacharacters, preventing user input from changing search meaning.
    pattern = re.escape(search_string)
    return list(collection.find({"name": {"$regex": pattern, "$options": "i"}}, {"_id": 0, "name": 1}).sort("name", 1))

def main():
    client, collection = get_collection("activity_4_1_search")
    try:
        prepare_collection(collection.database, collection.name)
        collection.insert_many(load_seed(Path(__file__).with_name("products.json")))
        for phrase in ["wireLESS", "PHONE", "mouse", "does-not-exist"]:
            matches = [row["name"] for row in search_products(collection, phrase)]
            print(f"Search {phrase!r}: {matches}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
