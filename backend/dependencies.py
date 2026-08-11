from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DatabaseSession
from typing import Optional

try:
    from .database import get_db
    from .models import Session, User
    from .utils import SESSION_COOKIE_NAME, create_guest_session, is_session_valid
except ImportError:
    from database import get_db
    from models import Session, User
    from utils import SESSION_COOKIE_NAME, create_guest_session, is_session_valid


def get_or_create_context(
    response: Response,
    session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: DatabaseSession = Depends(get_db),
):
    session = None
    if session_id:
        session = db.query(Session).filter(Session.session_id == session_id).first()
    if not is_session_valid(session):
        return create_guest_session(db, response)
    user = db.query(User).filter(User.user_id == session.user_id, User.is_active.is_(True)).first()
    if user is None:
        return create_guest_session(db, response)
    return session, user


def get_current_context(
    session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: DatabaseSession = Depends(get_db),
):
    session = None
    if session_id:
        session = db.query(Session).filter(Session.session_id == session_id).first()
    if not is_session_valid(session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    user = db.query(User).filter(User.user_id == session.user_id, User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User unavailable")
    return session, user
