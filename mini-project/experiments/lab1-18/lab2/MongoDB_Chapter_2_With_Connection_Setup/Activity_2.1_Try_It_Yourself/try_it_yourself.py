"""
Activity 2.1 - Try It Yourself:
Compare MongoDB version and wire-protocol information on Atlas and Docker.
"""
import json
import os
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import PyMongoError

TARGETS = {
    "Atlas": os.getenv("ATLAS_URI"),
    "Docker": os.getenv("DOCKER_URI", "mongodb://localhost:27017"),
}

def inspect_server(name, uri):
    if not uri:
        print(f"{name}: ATLAS_URI is not set; skipped.")
        return None

    client = MongoClient(uri, serverSelectionTimeoutMS=7000)
    try:
        client.admin.command("ping")
        info = client.server_info()
        details = {
            "server": name,
            "version": info.get("version"),
            "maxWireVersion": info.get("maxWireVersion"),
            "minWireVersion": info.get("minWireVersion"),
            "storageEngines": info.get("storageEngines", []),
        }
        print(f"\n{name}")
        for key, value in details.items():
            if key != "server":
                print(f"{key}: {value}")
        return details
    except PyMongoError as exc:
        print(f"{name} error: {exc}")
        return {"server": name, "error": str(exc)}
    finally:
        client.close()

def main():
    results = [inspect_server(name, uri) for name, uri in TARGETS.items()]
    successful = [item for item in results if item and "version" in item]
    if len(successful) == 2:
        print("\nVersion comparison:")
        if successful[0]["version"] == successful[1]["version"]:
            print("Both MongoDB servers are running the same version.")
        else:
            print("The MongoDB servers are running different versions.")
    output_dir = Path(__file__).with_name("outputs")
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "activity_2_1_try_output.json", "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)
    print("\nDetails saved to activity_2_1_try_output.json.")

if __name__ == "__main__":
    main()
