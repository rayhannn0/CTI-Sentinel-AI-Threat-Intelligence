import json
from pathlib import Path

SEPARATOR = "=" * 76
SECTION_SEPARATOR = "-" * 76


def load_activity():
    json_path = Path(__file__).with_name("activity_1_1.json")
    with json_path.open("r", encoding="utf-8") as json_file:
        return json.load(json_file)


def print_activity(activity):
    print(SEPARATOR)
    print(activity["activity"])
    print(SEPARATOR)
    print(f'{"PRODUCT":<18} {"FAMILY":<31} BEST-FOR SUMMARY')
    print(SECTION_SEPARATOR)

    for item in activity["products"]:
        print(
            f'{item["product"]:<18} '
            f'{item["family"]:<31} '
            f'{item["best_for"]}'
        )
        print(f'Reason: {item["reason"]}')
        print(f'Limitation: {item["limitation"]}')
        print(SECTION_SEPARATOR)


if __name__ == "__main__":
    print_activity(load_activity())
