"""Shared MongoDB connection. All collections appear under lab6 in Compass."""
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "lab6"

def get_db():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client, client[DATABASE_NAME]

if __name__ == "__main__":
    try:
        client, db = get_db()
        print("Connected to MongoDB | Database: " + db.name)
        print("Collections: " + ", ".join(db.list_collection_names()))
        client.close()
    except PyMongoError as exc:
        raise SystemExit(f"MongoDB connection failed: {exc}. Start mongod or check MONGODB_URI.")
