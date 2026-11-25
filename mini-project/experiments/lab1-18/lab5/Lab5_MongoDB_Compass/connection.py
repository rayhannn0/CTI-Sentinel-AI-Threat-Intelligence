"""One shared MongoDB connection for every Chapter 5 activity."""
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "lab5"

def get_database():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client, client[DATABASE_NAME]

if __name__ == "__main__":
    try:
        client, db = get_database()
        print(f"Connected to MongoDB | Database: {db.name}")
        print("Collections:", ", ".join(db.list_collection_names()) or "none yet")
        client.close()
    except ServerSelectionTimeoutError as exc:
        raise SystemExit("MongoDB server unavailable. Start mongod and connect Compass to localhost:27017. " + str(exc))
