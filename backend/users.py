from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session as DatabaseSession

try:
    from .database import get_db
    from .dependencies import get_current_user
    from .food_data import calculate_totals, targets_payload
    from .models import FoodEntry
    from .schemas import TargetUpdate
except ImportError:
    from database import get_db
    from dependencies import get_current_user
    from food_data import calculate_totals, targets_payload
    from models import FoodEntry
    from schemas import TargetUpdate


router = APIRouter(tags=["user"])


@router.patch("/users/me/targets")
def update_targets(
    payload: TargetUpdate,
    user=Depends(get_current_user),
    db: DatabaseSession = Depends(get_db),
):
    user.calorie_target = payload.calorie_target
    user.protein_target = payload.protein_target
    user.carbs_target = payload.carbs_target
    user.fat_target = payload.fat_target
    db.commit()
    return {"message": "Targets updated", "targets": targets_payload(user)}


@router.get("/users/me/statistics")
def get_statistics(
    user=Depends(get_current_user),
    db: DatabaseSession = Depends(get_db),
):
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


@router.get("/statistics")
def get_period_statistics(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user=Depends(get_current_user),
    db: DatabaseSession = Depends(get_db),
):
    selected_end = end_date or date.today()
    selected_start = start_date or (selected_end - timedelta(days=6))
    if selected_start > selected_end:
        raise HTTPException(status_code=422, detail="End date must be on or after the start date")

    entries = db.query(FoodEntry).filter(
        FoodEntry.user_id == user.user_id,
        FoodEntry.logged_on >= selected_start,
        FoodEntry.logged_on <= selected_end,
    ).all()
    totals = calculate_totals(entries)
    tracked_days = len({entry.logged_on for entry in entries})
    daily_averages = {
        key: round(value / tracked_days, 1) if tracked_days else 0
        for key, value in totals.items()
    }
    return {
        "start_date": selected_start.isoformat(),
        "end_date": selected_end.isoformat(),
        "entry_count": len(entries),
        "tracked_days": tracked_days,
        "totals": totals,
        "daily_averages": daily_averages,
    }
