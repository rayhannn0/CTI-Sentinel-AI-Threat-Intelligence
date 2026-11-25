"""MongoDB connection shared by all Lab 10 activities; run inside Compose labrunner."""
import os
from pymongo import MongoClient

URI = os.getenv('MONGO_URI', 'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs10')
DB_NAME = os.getenv('MONGO_DB', 'lab10')

def get_client():
    c = MongoClient(URI, serverSelectionTimeoutMS=12000, retryWrites=True)
    c.admin.command('ping')
    return c

def get_db(client):
    return client[DB_NAME]
