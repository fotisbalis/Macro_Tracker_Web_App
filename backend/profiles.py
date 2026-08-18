from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DatabaseSession

try:
    from .database import get_db
    from .food_data import targets_payload
    from .models import User
    from .profile_state import clear_active_user, get_active_user_id, set_active_user_id
    from .schemas import ProfileCreate, ProfileSelect
except ImportError:
    from database import get_db
    from food_data import targets_payload
    from models import User
    from profile_state import clear_active_user, get_active_user_id, set_active_user_id
    from schemas import ProfileCreate, ProfileSelect


router = APIRouter(prefix="/profiles", tags=["local profiles"])


def profile_payload(user: User) -> dict:
    return {
        "user_id": user.user_id,
        "user_name": user.user_name,
        "is_active": user.is_active,
        "targets": targets_payload(user),
    }


def active_profile(db: DatabaseSession):
    user_id = get_active_user_id()
    if user_id is None:
        return None
    user = db.query(User).filter(
        User.user_id == user_id,
        User.is_active.is_(True),
    ).first()
    if user is None:
        clear_active_user()
    return user


@router.get("")
def list_profiles(db: DatabaseSession = Depends(get_db)):
    users = db.query(User).filter(
        User.is_active.is_(True),
        func.length(func.trim(User.user_name)) > 0,
    ).order_by(func.lower(User.user_name), User.user_id).all()
    return {"users": [profile_payload(user) for user in users]}


@router.get("/current")
def get_current_profile(db: DatabaseSession = Depends(get_db)):
    user = active_profile(db)
    return {"user": profile_payload(user) if user else None}


@router.post("")
def create_profile(payload: ProfileCreate, db: DatabaseSession = Depends(get_db)):
    duplicate = db.query(User).filter(
        func.lower(User.user_name) == payload.user_name.lower()
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="That user name already exists")

    user = User(user_name=payload.user_name)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="That user name already exists") from exc
    db.refresh(user)
    set_active_user_id(user.user_id)
    return {
        "message": f"Created profile {user.user_name}.",
        "user": profile_payload(user),
    }


@router.post("/select")
def select_profile(payload: ProfileSelect, db: DatabaseSession = Depends(get_db)):
    user = db.query(User).filter(
        User.user_id == payload.user_id,
        User.is_active.is_(True),
        func.length(func.trim(User.user_name)) > 0,
    ).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Local profile not found")
    set_active_user_id(user.user_id)
    return {
        "message": f"Welcome, {user.user_name}.",
        "user": profile_payload(user),
    }


@router.post("/deselect")
def deselect_profile():
    clear_active_user()
    return {"message": "Choose a local profile to continue"}
