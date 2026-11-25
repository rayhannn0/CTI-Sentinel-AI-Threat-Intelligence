import os
from pymongo import MongoClient

def client():
    return MongoClient(os.getenv("MONGO_URI", "mongodb://127.0.0.1:27517/?directConnection=true"), serverSelectionTimeoutMS=15000)
