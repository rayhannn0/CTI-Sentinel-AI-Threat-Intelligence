from pymongo import MongoClient

print("Checking MongoDB connection...")

try:
    client = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    print("SUCCESS: MongoDB connected!")

    db = client["NoSQL_Lab"]
    print("Database:", db.name)

    client.close()

except Exception as error:
    print("MongoDB connection failed!")
    print("Reason:", error)
