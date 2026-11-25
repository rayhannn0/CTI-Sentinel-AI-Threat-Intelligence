import json
from pathlib import Path

json_path = Path(__file__).with_name("activity_1_2.json")
data = json.loads(json_path.read_text(encoding="utf-8"))

print("=" * 76)
print(data["activity"])
print("=" * 76)
print("RIDE-SHARING APPLICATION")
for item in data["ride_sharing"]:
    print(f'\n{item["domain"]} -> {item["family"]}')
    print("Why:", item["reason"])

print("\nSOCIAL MEDIA ANALYTICS")
for domain, details in data["social_analytics"].items():
    print(f'\n{domain.replace("_", " ").title()} -> {details["family"]}')
    print("Why:", details["reason"])
