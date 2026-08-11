import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Response

try:
    from .models import FoodEntry, Session, User, UserType
except ImportError:
    from models import FoodEntry, Session, User, UserType


SESSION_COOKIE_NAME = "macro_tracker_session"
PASSWORD_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    )


def verify_password(password: str, encoded: Optional[str]) -> bool:
    if not encoded:
        return False
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            base64.urlsafe_b64decode(salt.encode()),
            int(iterations),
        )
        return hmac.compare_digest(base64.urlsafe_b64encode(digest).decode(), expected)
    except (TypeError, ValueError):
        return False


def set_session_cookie(response: Response, session_id: str) -> None:
    secure = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=30 * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=secure,
    )


def create_guest_session(db, response: Response) -> tuple[Session, User]:
    token = os.urandom(6).hex()
    user = User(user_name=f"guest_{token}", user_type=UserType.GUEST.value)
    db.add(user)
    db.flush()
    session = Session(
        user_id=user.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    set_session_cookie(response, session.session_id)
    return session, user


def create_signed_session(db, response: Response, user: User) -> Session:
    session = Session(
        user_id=user.user_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    set_session_cookie(response, session.session_id)
    return session


def is_session_valid(session: Optional[Session]) -> bool:
    if session is None or not session.is_active:
        return False
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)


def transfer_guest_entries(db, guest_user_id: int, signed_user_id: int) -> None:
    db.query(FoodEntry).filter(FoodEntry.user_id == guest_user_id).update(
        {FoodEntry.user_id: signed_user_id, FoodEntry.session_id: None},
        synchronize_session=False,
    )


def user_payload(user: User, session: Session) -> dict:
    return {
        "session": {
            "session_id": session.session_id,
            "expires_at": session.expires_at,
            "is_active": session.is_active,
        },
        "user": {
            "user_id": user.user_id,
            "user_name": "Guest" if user.user_type == UserType.GUEST.value else user.user_name,
            "email": user.email,
            "user_type": user.user_type,
            "is_active": user.is_active,
            "targets": {
                "calories": user.calorie_target,
                "protein": user.protein_target,
                "carbs": user.carbs_target,
                "fat": user.fat_target,
            },
        },
    }
