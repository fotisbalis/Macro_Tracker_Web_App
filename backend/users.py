from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session as DatabaseSession

try:
    from .database import get_db
    from .dependencies import get_or_create_context
    from .food_data import targets_payload
    from .models import FoodEntry
    from .schemas import TargetUpdate
except ImportError:
    from database import get_db
    from dependencies import get_or_create_context
    from food_data import targets_payload
    from models import FoodEntry
    from schemas import TargetUpdate


router = APIRouter(tags=["user"])


@router.patch("/users/me/targets")
def update_targets(
    payload: TargetUpdate,
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    _session, user = context
    user.calorie_target = payload.calorie_target
    user.protein_target = payload.protein_target
    user.carbs_target = payload.carbs_target
    user.fat_target = payload.fat_target
    db.commit()
    return {"message": "Targets updated", "targets": targets_payload(user)}


@router.get("/users/me/statistics")
def get_statistics(
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    _session, user = context
    entry_count = db.query(func.count(FoodEntry.entry_id)).filter(
        FoodEntry.user_id == user.user_id
    ).scalar() or 0
    day_count = db.query(func.count(func.distinct(FoodEntry.logged_on))).filter(
        FoodEntry.user_id == user.user_id
    ).scalar() or 0
    total_calories = db.query(func.sum(FoodEntry.calories)).filter(
        FoodEntry.user_id == user.user_id
    ).scalar() or 0
    return {
        "entry_count": entry_count,
        "day_count": day_count,
        "average_daily_calories": round(total_calories / day_count, 1) if day_count else 0,
    }

