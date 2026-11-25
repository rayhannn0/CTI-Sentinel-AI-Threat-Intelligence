import json
from pathlib import Path

json_path = Path(__file__).with_name("try_it_yourself.json")
data = json.loads(json_path.read_text(encoding="utf-8"))

print("=" * 76)
print(data["activity"])
print("=" * 76)
for item in data["domains"]:
    print(f'\n{item["domain"]} -> {item["family"]}')
    print(item["reason"])
print("\nOVERALL MAPPING")
print(data["summary"])
