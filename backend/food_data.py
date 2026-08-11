from collections import defaultdict

try:
    from .models import FoodEntry, User
except ImportError:
    from models import FoodEntry, User


def serialize_entry(entry: FoodEntry) -> dict:
    return {
        "entry_id": entry.entry_id,
        "food_name": entry.food_name,
        "quantity": round(entry.quantity, 1),
        "unit": entry.unit,
        "calories": round(entry.calories, 1),
        "protein": round(entry.protein, 1),
        "carbs": round(entry.carbs, 1),
        "fat": round(entry.fat, 1),
        "source": entry.source,
        "logged_on": entry.logged_on.isoformat(),
        "created_at": entry.created_at.isoformat(),
    }


def calculate_totals(entries: list) -> dict:
    return {
        "calories": round(sum(item.calories for item in entries), 1),
        "protein": round(sum(item.protein for item in entries), 1),
        "carbs": round(sum(item.carbs for item in entries), 1),
        "fat": round(sum(item.fat for item in entries), 1),
    }


def targets_payload(user: User) -> dict:
    return {
        "calories": round(user.calorie_target, 1),
        "protein": round(user.protein_target, 1),
        "carbs": round(user.carbs_target, 1),
        "fat": round(user.fat_target, 1),
    }


def group_entries_by_day(entries: list) -> list:
    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry.logged_on].append(entry)
    return [
        {
            "date": day.isoformat(),
            "totals": calculate_totals(day_entries),
            "entries": [serialize_entry(entry) for entry in day_entries],
        }
        for day, day_entries in sorted(grouped.items(), reverse=True)
    ]

