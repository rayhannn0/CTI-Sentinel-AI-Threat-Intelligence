"""
Shared MongoDB connection examples for Atlas and local Docker.
Set environment variables before running the activity scripts.
"""
import os
from pymongo import MongoClient

DOCKER_URI = os.getenv("DOCKER_URI", "mongodb://localhost:27017")
ATLAS_URI = os.getenv("ATLAS_URI")

def connect_docker():
    """Connect to local MongoDB running in Docker."""
    client = MongoClient(DOCKER_URI, serverSelectionTimeoutMS=7000)
    client.admin.command("ping")
    print("Connected successfully to Docker MongoDB:", client.server_info()["version"])
    return client

def connect_atlas():
    """Connect to MongoDB Atlas using your own Atlas connection string."""
    if not ATLAS_URI:
        raise RuntimeError(
            "ATLAS_URI is missing. Set it in your terminal using the Atlas URI "
            "from MongoDB Atlas > Connect > Drivers."
        )
    client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    print("Connected successfully to MongoDB Atlas:", client.server_info()["version"])
    return client

if __name__ == "__main__":
    # Test Docker connection
    docker_client = None
    atlas_client = None
    try:
        docker_client = connect_docker()
    except Exception as exc:
        print("Docker connection error:", exc)
    try:
        atlas_client = connect_atlas()
    except Exception as exc:
        print("Atlas connection error:", exc)
    finally:
        if docker_client:
            docker_client.close()
        if atlas_client:
            atlas_client.close()
