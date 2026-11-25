"""
Activity 2.2: Increase the price of every book published before 2010 by 10%.
Run against local Docker MongoDB by default. Set MONGODB_URI to use Atlas instead.
"""
import json
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import PyMongoError

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "chapter2_library"
COLLECTION_NAME = "books"

def main():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=7000)
    try:
        client.admin.command("ping")
        collection = client[DATABASE_NAME][COLLECTION_NAME]

        # Reload sample data so repeated runs always start from original prices.
        with open(Path(__file__).with_name("activity_2_2.json"), encoding="utf-8") as file:
            books = json.load(file)
        collection.delete_many({})
        collection.insert_many(books)

        print("Books before update:")
        for book in collection.find({}, {"_id": 0}).sort("published_year", 1):
            print(book)

        result = collection.update_many(
            {"published_year": {"$lt": 2010}},
            {"$mul": {"price": 1.10}}
        )
        print(f"\nMatched documents: {result.matched_count}")
        print(f"Modified documents: {result.modified_count}")

        print("\nBooks after 10% price increase (published before 2010):")
        for book in collection.find({}, {"_id": 0}).sort("published_year", 1):
            print(book)

        print(f"\nVerify in MongoDB Compass: database={DATABASE_NAME}, collection={COLLECTION_NAME}")
    except (PyMongoError, OSError, json.JSONDecodeError) as exc:
        print(f"Operation failed: {exc}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
