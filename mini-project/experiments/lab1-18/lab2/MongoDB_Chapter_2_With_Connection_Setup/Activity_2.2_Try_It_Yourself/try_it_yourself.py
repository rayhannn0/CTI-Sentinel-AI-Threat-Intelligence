"""
Activity 2.2 - Try It Yourself:
Additional exercise: increase prices by 5% for books published from 2010
through 2015 (inclusive). Books outside this year range remain unchanged.
"""
import json
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import PyMongoError

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "chapter2_library_try"
COLLECTION_NAME = "books"

def main():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=7000)
    try:
        client.admin.command("ping")
        collection = client[DATABASE_NAME][COLLECTION_NAME]

        with open(Path(__file__).with_name("try_it_yourself.json"), encoding="utf-8") as file:
            books = json.load(file)
        collection.delete_many({})
        collection.insert_many(books)

        result = collection.update_many(
            {"published_year": {"$gte": 2010, "$lte": 2015}},
            {"$mul": {"price": 1.05}}
        )
        print(f"Matched documents: {result.matched_count}")
        print(f"Modified documents: {result.modified_count}")
        print("\nFinal book records:")
        for book in collection.find({}, {"_id": 0}).sort("published_year", 1):
            print(book)

        print(f"\nVerify in Compass: database={DATABASE_NAME}, collection={COLLECTION_NAME}")
    except (PyMongoError, OSError, json.JSONDecodeError) as exc:
        print(f"Operation failed: {exc}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
