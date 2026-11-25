"""Shared MongoDB connection. All Lab 7 collections appear in Compass database lab7."""
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
DATABASE_NAME = os.getenv("MONGODB_DB", "lab7")
_client = None

def get_db():
    global _client
    if _client is None:
        candidate = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        try:
            candidate.admin.command("ping")
        except Exception:
            candidate.close()
            raise
        _client = candidate
    return _client[DATABASE_NAME]

def close_connection():
    global _client
    if _client is not None:
        _client.close()
        _client = None

if __name__ == "__main__":
    try:
        db = get_db()
        print(f"MongoDB connected | Compass database: {db.name}")
        print("Collections:", ", ".join(db.list_collection_names()) or "(empty; run seed_db.py)")
    except PyMongoError as exc:
        print("MongoDB connection failed:", exc)
        print("Check that MongoDB Server is running. Compass alone does not start the server.")
        raise SystemExit(1)
    finally:
        close_connection()
