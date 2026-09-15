from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from .database import get_db
    from .dependencies import get_current_user
    from .food_data import quantity_values, serialize_entry
    from .models import FavoriteFood, FoodEntry
    from .schemas import FavoriteFoodLog
except ImportError:
    from database import get_db
    from dependencies import get_current_user
    from food_data import quantity_values, serialize_entry
    from models import FavoriteFood, FoodEntry
    from schemas import FavoriteFoodLog


router = APIRouter(prefix="/favorites", tags=["favorite foods"])
FOOD_FIELDS = ("food_name", "quantity", "unit", "calories", "protein", "carbs", "fat", "source")


def food_values(food):
    return {**{field: getattr(food, field) for field in FOOD_FIELDS}, **quantity_values(food)}


def favorite_payload(food):
    return {"favorite_id": food.favorite_id, **food_values(food)}


def find_favorite(db, user_id, favorite_id):
    food = db.query(FavoriteFood).filter_by(user_id=user_id, favorite_id=favorite_id).first()
    if food is None:
        raise HTTPException(status_code=404, detail="Favorite food not found")
    return food


@router.get("")
def list_favorites(user=Depends(get_current_user), db: Session = Depends(get_db)):
    foods = db.query(FavoriteFood).filter_by(user_id=user.user_id).order_by(
        FavoriteFood.food_name, FavoriteFood.favorite_id
    ).all()
    return {"favorites": [favorite_payload(food) for food in foods]}


@router.post("/from-entry/{entry_id}")
def save_favorite(entry_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    entry = db.query(FoodEntry).filter_by(user_id=user.user_id, entry_id=entry_id).first()
    if entry is None:
        raise HTTPException(status_code=404, detail="Food entry not found")
    values = food_values(entry)
    candidates = db.query(FavoriteFood).filter_by(
        user_id=user.user_id, **{key: value for key, value in values.items() if key not in ("quantity", "unit")}
    ).all()
    favorite = next((food for food in candidates if food_values(food) == values), None)
    if favorite is None:
        favorite = FavoriteFood(user_id=user.user_id, **values)
        db.add(favorite)
        db.commit()
        db.refresh(favorite)
    return {"message": "Saved to Favorites", "favorite": favorite_payload(favorite)}


@router.post("/{favorite_id}/log")
def log_favorite(
    favorite_id: int, payload: FavoriteFoodLog,
    user=Depends(get_current_user), db: Session = Depends(get_db),
):
    favorite = find_favorite(db, user.user_id, favorite_id)
    values = food_values(favorite)
    if payload.quantity is not None:
        if values["unit"] == "portion" and not payload.quantity.is_integer():
            raise HTTPException(status_code=422, detail="Quantity must be a whole number of portions (1, 2, 3, …)")
        scale = Decimal(str(payload.quantity)) / Decimal(str(values["quantity"]))
        values["quantity"] = payload.quantity
        for field in ("calories", "protein", "carbs", "fat"):
            values[field] = float((Decimal(str(values[field])) * scale).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            ))
    entry = FoodEntry(
        user_id=user.user_id, logged_on=payload.logged_on or date.today(), **values
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"message": f"Added {entry.food_name} to {entry.logged_on:%d/%m/%Y}.", "entry": serialize_entry(entry)}


@router.delete("/{favorite_id}")
def delete_favorite(favorite_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    favorite = find_favorite(db, user.user_id, favorite_id)
    db.delete(favorite)
    db.commit()
    return {"message": "Removed from Favorites"}
