from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DatabaseSession

try:
    from .database import get_db
    from .dependencies import get_or_create_context
    from .food_data import calculate_totals, serialize_entry, targets_payload
    from .models import FoodEntry
    from .schemas import FoodEntryCreate, ManualFoodEntryCreate
    from .services.mock_ai import ai_service
except ImportError:
    from database import get_db
    from dependencies import get_or_create_context
    from food_data import calculate_totals, serialize_entry, targets_payload
    from models import FoodEntry
    from schemas import FoodEntryCreate, ManualFoodEntryCreate
    from services.mock_ai import ai_service


router = APIRouter(tags=["food entries"])


def entries_for_day(db, user_id: int, selected_date: date):
    return db.query(FoodEntry).filter(
        FoodEntry.user_id == user_id,
        FoodEntry.logged_on == selected_date,
    ).order_by(FoodEntry.created_at.desc()).all()


@router.post("/foods/analyze")
async def analyze_food(
    payload: FoodEntryCreate,
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    session, user = context
    result = await ai_service.analyze_food(payload.food_name, payload.quantity)
    result = result.model_copy(update={
        "food_name": payload.food_name,
        "quantity": payload.quantity,
        "unit": "g",
    })

    entry = FoodEntry(
        session_id=session.session_id,
        user_id=user.user_id,
        logged_on=payload.logged_on or date.today(),
        **result.model_dump(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    day_entries = entries_for_day(db, user.user_id, entry.logged_on)
    return {
        "message": f"Added {entry.quantity:g}g of {entry.food_name}.",
        "entry": serialize_entry(entry),
        "totals": calculate_totals(day_entries),
        "targets": targets_payload(user),
    }


@router.post("/foods/manual")
def add_manual_food(
    payload: ManualFoodEntryCreate,
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    session, user = context
    food_name = payload.food_name or f"manual_meal_{uuid4()}"
    quantity = payload.quantity if payload.quantity is not None else 0.0

    entry = FoodEntry(
        session_id=session.session_id,
        user_id=user.user_id,
        food_name=food_name,
        quantity=quantity,
        unit="g",
        calories=payload.calories,
        protein=payload.protein,
        carbs=payload.carbs,
        fat=payload.fat,
        source="manual",
        logged_on=payload.logged_on or date.today(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    day_entries = entries_for_day(db, user.user_id, entry.logged_on)
    return {
        "message": f"Added manual meal {entry.food_name}.",
        "entry": serialize_entry(entry),
        "totals": calculate_totals(day_entries),
        "targets": targets_payload(user),
    }


@router.get("/days/today")
def get_today(
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    _session, user = context
    today = date.today()
    entries = entries_for_day(db, user.user_id, today)
    return {
        "date": today.isoformat(),
        "entries": [serialize_entry(entry) for entry in entries],
        "totals": calculate_totals(entries),
        "targets": targets_payload(user),
    }


@router.delete("/foods/{entry_id}")
def delete_food(
    entry_id: int,
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    _session, user = context
    entry = db.query(FoodEntry).filter(
        FoodEntry.entry_id == entry_id,
        FoodEntry.user_id == user.user_id,
    ).first()
    if entry is None:
        raise HTTPException(status_code=404, detail="Food entry not found")
    selected_date = entry.logged_on
    db.delete(entry)
    db.commit()
    entries = entries_for_day(db, user.user_id, selected_date)
    return {"message": "Food removed", "totals": calculate_totals(entries)}
