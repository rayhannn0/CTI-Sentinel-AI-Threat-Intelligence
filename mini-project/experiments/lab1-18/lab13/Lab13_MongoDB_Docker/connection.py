import os
from pymongo import MongoClient

def client():
    pwd=os.environ['ROOT_PASSWORD']
    return MongoClient('mongodb://mongo1:27017,mongo2:27017,mongo3:27017/',
      username='lab13_admin',password=pwd,authSource='admin',replicaSet='rs13',
      serverSelectionTimeoutMS=10000,connectTimeoutMS=3000,retryWrites=True)
