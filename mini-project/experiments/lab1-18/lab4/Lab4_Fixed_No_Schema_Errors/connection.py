"""Single MongoDB connection for all four Lab 4 exercises.
MongoDB Compass: connect to mongodb://localhost:27017 and refresh.
You will see database `lab4`, containing four named collections.
"""
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "lab4"

def get_collection(collection_name):
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except PyMongoError as exc:
        client.close()
        raise ConnectionError(
            "Cannot reach MongoDB. Start the MongoDB server, then check "
            "the URI in connection.py (default: mongodb://localhost:27017/)."
        ) from exc
    print(f"Connected to MongoDB | Database: {DATABASE_NAME} | Collection: {collection_name}")
    return client, client[DATABASE_NAME][collection_name]

if __name__ == "__main__":
    client, collection = get_collection("connection_test")
    print("Connection OK. Run the activity scripts to create their collections.")
    client.close()
