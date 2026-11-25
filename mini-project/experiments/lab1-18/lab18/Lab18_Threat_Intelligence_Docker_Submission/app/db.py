import os
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase

def mongo_client(): return MongoClient(os.getenv('MONGO_URI','mongodb://mongo:27017'), serverSelectionTimeoutMS=15000)
def cassandra_cluster(): return Cluster([os.getenv('CASSANDRA_HOST','cassandra')], connect_timeout=20)
def graph_driver(): return GraphDatabase.driver(os.getenv('NEO4J_URI','bolt://neo4j:7687'), auth=(os.getenv('NEO4J_USER','neo4j'), os.getenv('NEO4J_PASSWORD','lab18securepassword')), max_connection_pool_size=15)
