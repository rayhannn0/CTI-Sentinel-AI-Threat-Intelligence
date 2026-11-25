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

def product_page(collection, page, per_page):
    if page < 1 or per_page < 1:
        raise ValueError("page and per_page must be positive")
    return list(collection.find({}, {"_id": 0}).sort("name", 1).skip((page-1)*per_page).limit(per_page))

def main():
    client, collection = get_collection("lab_4_1_products")
    try:
        prepare_collection(collection.database, collection.name)
        collection.insert_many(load_seed(Path(__file__).with_name("products.json")))
        queries = {
            "Price between 20 and 50 inclusive": {"price": {"$gte": 20, "$lte": 50}},
            "Out of stock": {"stock": 0},
            "Out of stock OR price above 100": {"$or": [{"stock": 0}, {"price": {"$gt": 100}}]},
            "In stock AND premium": {"$and": [{"stock": {"$gt": 0}}, {"tags": "premium"}]},
            "Both electronics and wireless": {"tags": {"$all": ["electronics", "wireless"]}},
            "Exactly two tags": {"tags": {"$size": 2}},
        }
        print("Inserted:", collection.count_documents({}))
        for label, query in queries.items():
            print("\n" + label + ":")
            print([item["name"] for item in collection.find(query, {"name": 1, "_id": 0}).sort("name", 1)])
        print("\nPagination (page 2, 3 items):")
        print([item["name"] for item in product_page(collection, 2, 3)])
        # CRUD demonstration: create, read, update, delete a temporary record.
        collection.insert_one({"sku":"TEMP", "name":"Temporary Demo", "price":1.0, "stock":0, "tags":[]})
        print("CRUD read:", collection.find_one({"sku":"TEMP"}, {"_id":0}))
        collection.update_one({"sku":"TEMP"}, {"$set":{"price":2.0}})
        print("CRUD updated price:", collection.find_one({"sku":"TEMP"})["price"])
        collection.delete_one({"sku":"TEMP"})
        print("CRUD deleted temporary product")
    finally:
        client.close()

if __name__ == "__main__":
    main()
