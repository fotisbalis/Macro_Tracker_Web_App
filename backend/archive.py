from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DatabaseSession

try:
    from .database import get_db
    from .dependencies import get_or_create_context
    from .food_data import group_entries_by_day
    from .models import FoodEntry
except ImportError:
    from database import get_db
    from dependencies import get_or_create_context
    from food_data import group_entries_by_day
    from models import FoodEntry


router = APIRouter(tags=["archive"])


@router.get("/archive")
def get_archive(
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    _session, user = context
    entries = db.query(FoodEntry).filter(
        FoodEntry.user_id == user.user_id,
    ).order_by(FoodEntry.logged_on.desc(), FoodEntry.created_at.desc()).all()
    return {"days": group_entries_by_day(entries)}

