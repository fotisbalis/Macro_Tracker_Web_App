from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DatabaseSession

try:
    from .database import get_db
    from .dependencies import get_current_user
    from .food_data import calculate_totals, serialize_entry, targets_payload
    from .models import FoodEntry
    from .schemas import FoodEntryCreate, ManualFoodEntryCreate
    from .services.ai_service import AIServiceError
    from .services.provider import ai_service
except ImportError:
    from database import get_db
    from dependencies import get_current_user
    from food_data import calculate_totals, serialize_entry, targets_payload
    from models import FoodEntry
    from schemas import FoodEntryCreate, ManualFoodEntryCreate
    from services.ai_service import AIServiceError
    from services.provider import ai_service


router = APIRouter(tags=["food entries"])


def entries_for_day(db, user_id: int, selected_date: date):
    return db.query(FoodEntry).filter(
        FoodEntry.user_id == user_id,
        FoodEntry.logged_on == selected_date,
    ).order_by(FoodEntry.created_at.desc()).all()


@router.post("/foods/analyze")
async def analyze_food(
    payload: FoodEntryCreate,
    user=Depends(get_current_user),
    db: DatabaseSession = Depends(get_db),
):
    try:
        result = await ai_service.analyze_food(payload.food_name, payload.quantity)
    except AIServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "The AI could not estimate this meal. Please try again or enter "
                "the macros manually."
            ),
        ) from exc
    result = result.model_copy(update={
        "food_name": payload.food_name,
        "quantity": payload.quantity,
        "unit": "g",
    })

    entry = FoodEntry(
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
    user=Depends(get_current_user),
    db: DatabaseSession = Depends(get_db),
):
    food_name = payload.food_name or f"manual_meal_{uuid4()}"
    quantity = payload.quantity if payload.quantity is not None else 0.0

    entry = FoodEntry(
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


@router.post("/foods/{entry_id}/add-to-today")
def add_archived_food_to_today(
    entry_id: int,
    user=Depends(get_current_user),
    db: DatabaseSession = Depends(get_db),
):
    archived_entry = db.query(FoodEntry).filter(
        FoodEntry.entry_id == entry_id,
        FoodEntry.user_id == user.user_id,
    ).first()
    if archived_entry is None:
        raise HTTPException(status_code=404, detail="Food entry not found")
    if archived_entry.logged_on >= date.today():
        raise HTTPException(status_code=400, detail="Only meals from previous days can be added")

    copied_entry = FoodEntry(
        user_id=user.user_id,
        food_name=archived_entry.food_name,
        quantity=archived_entry.quantity,
        unit=archived_entry.unit,
        calories=archived_entry.calories,
        protein=archived_entry.protein,
        carbs=archived_entry.carbs,
        fat=archived_entry.fat,
        source=archived_entry.source,
        logged_on=date.today(),
    )
    db.add(copied_entry)
    db.commit()
    db.refresh(copied_entry)

    today_entries = entries_for_day(db, user.user_id, date.today())
    return {
        "message": f"Added {copied_entry.food_name} to today's totals.",
        "entry": serialize_entry(copied_entry),
        "totals": calculate_totals(today_entries),
        "targets": targets_payload(user),
    }


@router.get("/days/today")
def get_today(
    user=Depends(get_current_user),
    db: DatabaseSession = Depends(get_db),
):
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
    user=Depends(get_current_user),
    db: DatabaseSession = Depends(get_db),
):
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
