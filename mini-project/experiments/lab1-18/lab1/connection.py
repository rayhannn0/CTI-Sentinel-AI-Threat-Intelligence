
from pymongo import MongoClient

try:
    print("Checking MongoDB connection...")

    client = MongoClient("mongodb://localhost:27017/")
    client.admin.command("ping")

    print("SUCCESS: MongoDB connected!")

    db = client["NoSQL_Lab"]
    collection = db["students"]

    result = collection.insert_one({
        "name": "Rayz",
        "activity": "NoSQL Lab",
        "status": "Completed"
    })

    print("SUCCESS: Document inserted!")
    print("Inserted ID:", result.inserted_id)

    client.close()

except Exception as error:
    print("MongoDB connection failed!")
    print("Reason:", error)
