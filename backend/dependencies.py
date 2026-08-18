from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session as DatabaseSession

try:
    from .database import get_db
    from .models import User
    from .profile_state import clear_active_user, get_active_user_id
except ImportError:
    from database import get_db
    from models import User
    from profile_state import clear_active_user, get_active_user_id


def get_current_user(
    db: DatabaseSession = Depends(get_db),
):
    user_id = get_active_user_id()
    if user_id is None:
        raise HTTPException(status_code=409, detail="Select a local profile first")
    user = db.query(User).filter(
        User.user_id == user_id,
        User.is_active.is_(True),
    ).first()
    if user is None:
        clear_active_user()
        raise HTTPException(status_code=404, detail="Selected profile is unavailable")
    return user
