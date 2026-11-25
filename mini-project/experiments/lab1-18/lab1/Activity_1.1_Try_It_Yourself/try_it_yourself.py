import json
from pathlib import Path

json_path = Path(__file__).with_name("try_it_yourself.json")
data = json.loads(json_path.read_text(encoding="utf-8"))
product = data["product"]

print("=" * 72)
print(data["activity"])
print("=" * 72)
print("Product:", product["name"])
print("NoSQL family:", product["family"])
print("Classification:", product["classification"])
print("Reason:", product["reason"])
print("Best use case:", product["best_for"])
print("Limitation:", product["limitation"])
