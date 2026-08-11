from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session as DatabaseSession

try:
    from .database import get_db
    from .dependencies import get_or_create_context
    from .models import Session, User, UserType
    from .schemas import LoginRequest, SignupRequest
    from .utils import (
        create_guest_session,
        create_signed_session,
        hash_password,
        set_session_cookie,
        transfer_guest_entries,
        user_payload,
        verify_password,
    )
except ImportError:
    from database import get_db
    from dependencies import get_or_create_context
    from models import Session, User, UserType
    from schemas import LoginRequest, SignupRequest
    from utils import (
        create_guest_session,
        create_signed_session,
        hash_password,
        set_session_cookie,
        transfer_guest_entries,
        user_payload,
        verify_password,
    )


router = APIRouter(tags=["authentication"])


@router.get("/session/user")
def get_session_user(context=Depends(get_or_create_context)):
    session, user = context
    return user_payload(user, session)


@router.post("/signup")
def signup(
    payload: SignupRequest,
    response: Response,
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    session, current_user = context
    if current_user.user_type != UserType.GUEST.value:
        raise HTTPException(status_code=400, detail="You are already signed in")

    duplicate = db.query(User).filter(
        or_(User.email == payload.email, User.user_name == payload.user_name)
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Username or email is already in use")

    current_user.user_name = payload.user_name
    current_user.email = payload.email
    current_user.hashed_password = hash_password(payload.password)
    current_user.user_type = UserType.SIGNED.value
    session.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    db.commit()
    db.refresh(current_user)
    set_session_cookie(response, session.session_id)
    return user_payload(current_user, session)


@router.post("/login")
def login(
    payload: LoginRequest,
    response: Response,
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    guest_session, guest_user = context
    user = db.query(User).filter(
        User.email == payload.email.strip().lower(),
        User.user_type.in_([UserType.SIGNED.value, UserType.ADMIN.value]),
        User.is_active.is_(True),
    ).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if guest_user.user_type == UserType.GUEST.value and guest_user.user_id != user.user_id:
        transfer_guest_entries(db, guest_user.user_id, user.user_id)
    guest_session.is_active = False
    db.commit()
    new_session = create_signed_session(db, response, user)
    return user_payload(user, new_session)


@router.post("/logout")
def logout(
    response: Response,
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    session, _user = context
    session.is_active = False
    db.commit()
    guest_session, guest_user = create_guest_session(db, response)
    return user_payload(guest_user, guest_session)

