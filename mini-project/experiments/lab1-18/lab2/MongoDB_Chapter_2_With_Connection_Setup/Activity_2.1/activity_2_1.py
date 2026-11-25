"""
Activity 2.1: Connect to MongoDB Atlas and local Docker MongoDB.
Compare server version information using PyMongo's server_info() command.

Set ATLAS_URI before running. Local Docker MongoDB defaults to localhost:27017.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import PyMongoError

ATLAS_URI = os.getenv("ATLAS_URI")
DOCKER_URI = os.getenv("DOCKER_URI", "mongodb://localhost:27017")

def get_server_info(label, uri):
    if not uri:
        print(f"{label}: connection string is not configured; skipping.")
        return None

    client = MongoClient(uri, serverSelectionTimeoutMS=7000)
    try:
        client.admin.command("ping")
        info = client.server_info()  # Required server_info() command
        result = {
            "server": label,
            "version": info.get("version"),
            "gitVersion": info.get("gitVersion"),
            "maxWireVersion": info.get("maxWireVersion"),
            "ok": info.get("ok"),
        }
        print(f"\n{label} server information")
        print(f"MongoDB version : {result['version']}")
        print(f"Git version     : {result['gitVersion']}")
        print(f"Max wire version: {result['maxWireVersion']}")
        return result
    except PyMongoError as exc:
        print(f"{label} connection failed: {exc}")
        return {"server": label, "error": str(exc)}
    finally:
        client.close()

def main():
    results = {
        "activity": "2.1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "servers": [
            get_server_info("MongoDB Atlas", ATLAS_URI),
            get_server_info("Docker MongoDB", DOCKER_URI),
        ],
    }
    output_dir = Path(__file__).with_name("outputs")
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "activity_2_1_output.json", "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)
    print("\nComparison completed. Results saved to activity_2_1_output.json.")

if __name__ == "__main__":
    main()
