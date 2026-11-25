
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

try:
    client = MongoClient(
        "mongodb://localhost:27017/",
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    print("MongoDB connected successfully!")

    db = client["NoSQL_Lab"]
    print("Database:", db.name)

    client.close()

except ServerSelectionTimeoutError:
    print("MongoDB connection failed!")
    print("Make sure MongoDB Server is running.")
