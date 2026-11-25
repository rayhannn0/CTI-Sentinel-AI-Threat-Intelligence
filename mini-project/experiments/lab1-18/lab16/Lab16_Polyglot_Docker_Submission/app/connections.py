import os
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase


def mongo_client():
    return MongoClient(os.getenv("MONGO_URI", "mongodb://mongo:27017"), maxPoolSize=10, serverSelectionTimeoutMS=10000)


def cassandra_session():
    cluster = Cluster([os.getenv("CASSANDRA_HOST", "cassandra")], executor_threads=4)
    session = cluster.connect()
    return cluster, session


def neo4j_driver():
    return GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://neo4j:7687"), auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "lab16password")), max_connection_pool_size=10)
