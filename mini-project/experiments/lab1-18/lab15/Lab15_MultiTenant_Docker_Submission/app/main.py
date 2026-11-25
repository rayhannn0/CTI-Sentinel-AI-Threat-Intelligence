"""Lab 15.1: tenant-scoped CRUD, RBAC, JWT authentication, and MongoDB rate limiting."""
import os
import hashlib
import hmac
import secrets
from datetime import datetime, timezone, timedelta
from typing import Literal

import jwt
from bson import ObjectId
from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient, ReturnDocument, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from pydantic import BaseModel, Field

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
JWT_SECRET = os.environ.get("JWT_SECRET", "local-development-secret-change-before-publishing")
JWT_ALGORITHM = "HS256"
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "60"))
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["tasktracker"]
app = FastAPI(title="Lab 15 Multi-Tenant TaskTracker", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token")


@app.on_event("startup")
def setup_indexes():
    db.tasks.create_index([("tenant_id", ASCENDING), ("created_at", DESCENDING)])
    db.tasks.create_index([("tenant_id", ASCENDING), ("owner_id", ASCENDING)])
    db.users.create_index([("tenant_id", ASCENDING), ("username", ASCENDING)], unique=True)
    db.rate_limits.create_index("expires_at", expireAfterSeconds=0)
    db.rate_limits.create_index([("window_key", ASCENDING)], unique=True)


class Login(BaseModel):
    username: str
    password: str
    tenant_id: str


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: Literal["low", "medium", "high"] = "medium"


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: Literal["low", "medium", "high"] | None = None
    status: Literal["open", "in_progress", "done"] | None = None


def serialize(doc):
    return {"id": str(doc["_id"]), "tenant_id": doc["tenant_id"],
            "owner_id": doc["owner_id"], "title": doc["title"],
            "description": doc["description"], "priority": doc["priority"],
            "status": doc["status"], "created_at": doc["created_at"].isoformat()}


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return salt + "$" + digest.hex()


def verify_password(password, stored):
    try:
        salt, actual = stored.split("$", 1)
        return hmac.compare_digest(password_hash(password, salt).split("$", 1)[1], actual)
    except (ValueError, AttributeError):
        return False


@app.post("/auth/token")
def login(credentials: Login):
    user = db.users.find_one({"tenant_id": credentials.tenant_id, "username": credentials.username})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    payload = {"sub": str(user["_id"]), "tenant_id": user["tenant_id"],
               "exp": datetime.now(timezone.utc) + timedelta(hours=8)}
    return {"access_token": jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), "token_type": "bearer"}


def current_user(token: str = Depends(oauth2)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = db.users.find_one({"_id": ObjectId(payload["sub"]), "tenant_id": payload["tenant_id"]})
        if not user:
            raise ValueError("User missing")
        return {"id": str(user["_id"]), "tenant_id": user["tenant_id"], "role": user["role"]}
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")


def apply_rate_limit(user=Depends(current_user)):
    """Atomic fixed-minute counter; TTL is garbage collection, not enforcement."""
    now = datetime.now(timezone.utc)
    minute = int(now.timestamp() // 60)
    key = f'{user["tenant_id"]}:{user["id"]}:{minute}'
    expires = datetime.fromtimestamp((minute + 2) * 60, tz=timezone.utc)
    try:
        counter = db.rate_limits.find_one_and_update(
            {"window_key": key},
            {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": expires}},
            upsert=True, return_document=ReturnDocument.AFTER)
    except DuplicateKeyError:
        counter = db.rate_limits.find_one_and_update(
            {"window_key": key}, {"$inc": {"count": 1}}, return_document=ReturnDocument.AFTER)
    if counter["count"] > RATE_LIMIT:
        raise HTTPException(429, "Rate limit exceeded; retry next minute")
    return user


def scoped_query(user, task_id=None):
    query = {"tenant_id": user["tenant_id"]}
    if user["role"] != "admin":
        query["owner_id"] = user["id"]
    if task_id is not None:
        try:
            query["_id"] = ObjectId(task_id)
        except Exception:
            raise HTTPException(400, "Invalid task ID")
    return query


@app.get("/health")
def health():
    try:
        db.command("ping")
        return {"status": "ok", "database": "connected"}
    except Exception:
        raise HTTPException(503, "Database unavailable")


@app.post("/tasks/", status_code=201)
def create_task(task: TaskCreate, user=Depends(apply_rate_limit)):
    doc = {**task.model_dump(), "tenant_id": user["tenant_id"],
           "owner_id": user["id"], "status": "open", "created_at": datetime.now(timezone.utc)}
    doc["_id"] = db.tasks.insert_one(doc).inserted_id
    return serialize(doc)


@app.get("/tasks/")
def list_tasks(user=Depends(apply_rate_limit)):
    return [serialize(t) for t in db.tasks.find(scoped_query(user)).sort("created_at", DESCENDING)]


@app.get("/tasks/{task_id}")
def get_task(task_id: str, user=Depends(apply_rate_limit)):
    doc = db.tasks.find_one(scoped_query(user, task_id))
    if not doc:
        raise HTTPException(404, "Task not found")
    return serialize(doc)


@app.patch("/tasks/{task_id}")
def update_task(task_id: str, patch: TaskPatch, user=Depends(apply_rate_limit)):
    changes = patch.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        raise HTTPException(400, "No updates provided")
    doc = db.tasks.find_one_and_update(scoped_query(user, task_id), {"$set": changes}, return_document=ReturnDocument.AFTER)
    if not doc:
        raise HTTPException(404, "Task not found")
    return serialize(doc)


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, user=Depends(apply_rate_limit)):
    result = db.tasks.delete_one(scoped_query(user, task_id))
    if not result.deleted_count:
        raise HTTPException(404, "Task not found")
    return {"deleted": True}
