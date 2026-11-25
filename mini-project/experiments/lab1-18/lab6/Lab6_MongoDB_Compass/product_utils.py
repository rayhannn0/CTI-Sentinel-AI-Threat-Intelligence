"""Deterministic random product generation and explain-plan parsing."""
import random
from pymongo import InsertOne

CATEGORIES = ["Electronics", "Books", "Home", "Fitness", "Fashion", "Grocery"]
TAGS = ["wireless", "premium", "sale", "eco", "popular", "new", "portable", "durable"]

def generate_products(count, seed=2026, start=0):
    rng = random.Random(seed)
    for i in range(start, start + count):
        category = rng.choice(CATEGORIES)
        name = f"{category} Product {i:06d}"
        yield {
            "sku": f"SKU-{i:06d}", "name": name,
            "category": category, "price": round(rng.uniform(5, 1200), 2),
            "rating": round(rng.uniform(1, 5), 1),
            "stock": rng.randrange(0, 501),
            "tags": rng.sample(TAGS, rng.randint(1, 3))
        }

def insert_batches(collection, docs, batch_size=1000):
    batch = []
    for doc in docs:
        batch.append(doc)
        if len(batch) >= batch_size:
            collection.insert_many(batch, ordered=False)
            batch = []
    if batch:
        collection.insert_many(batch, ordered=False)

def workload():
    return [
        ("Category and price sort", {"category": "Electronics"}, {"price": 1, "_id": 0}, [("price", 1)], 15),
        ("Price range", {"price": {"$gte": 100, "$lte": 250}}, {"name": 1, "price": 1, "_id": 0}, None, 15),
        ("Tagged wireless", {"tags": "wireless"}, {"name": 1, "tags": 1, "_id": 0}, None, 15),
        ("High rating and in stock", {"rating": {"$gte": 4.5}, "stock": {"$gt": 0}}, {"name": 1, "rating": 1, "_id": 0}, None, 15),
        ("Name prefix", {"name": {"$regex": "^Electronics"}}, {"name": 1, "_id": 0}, None, 15),
    ]

def query_command(collection, filt, projection, sort, limit):
    cmd = {"find": collection.name, "filter": filt, "projection": projection, "limit": limit}
    if sort:
        cmd["sort"] = dict(sort)
    return cmd

def explain_find(db, collection, filt, projection, sort, limit):
    return db.command("explain", query_command(collection, filt, projection, sort, limit), verbosity="executionStats")

def plan_stages(explain):
    found = []
    def walk(item):
        if isinstance(item, dict):
            stage = item.get("stage")
            if isinstance(stage, str): found.append(stage)
            for value in item.values(): walk(value)
        elif isinstance(item, list):
            for val in item: walk(val)
    walk(explain.get("queryPlanner", {}).get("winningPlan", {}))
    return list(dict.fromkeys(found)) or ["(SBE plan / see full explain)"]

def describe(explain):
    stats = explain.get("executionStats", {})
    return f"stages={','.join(plan_stages(explain))} | totalDocsExamined={stats.get('totalDocsExamined', 'N/A')} | totalKeysExamined={stats.get('totalKeysExamined', 'N/A')} | executionTimeMillis={stats.get('executionTimeMillis', 'N/A')}"

def print_workload(db, collection, heading):
    print("\n" + heading)
    result = {}
    for label, filt, projection, sort, limit in workload():
        exp = explain_find(db, collection, filt, projection, sort, limit)
        result[label] = exp
        print(label + ": " + describe(exp))
    return result

def create_five_indexes(collection):
    collection.create_index([("category", 1), ("price", 1)], name="idx_category_price")
    collection.create_index("price", name="idx_price")
    collection.create_index("tags", name="idx_tags")
    collection.create_index([("rating", 1), ("stock", 1)], name="idx_rating_stock")
    collection.create_index("name", name="idx_name")
