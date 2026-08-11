import logging
from datetime import datetime, timedelta, timezone
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session as DatabaseSession

try:
    from .database import get_db
    from .dependencies import get_or_create_context
    from .email_verification import (
        confirm_pending_password_reset,
        confirm_pending_signup,
        consume_password_reset_token,
        create_pending_password_reset,
        create_pending_signup,
        generate_verification_code,
        send_verification_email,
    )
    from .models import Session, User, UserType
    from .schemas import (
        ChangePasswordRequest,
        ForgotPasswordStartRequest,
        ForgotPasswordVerificationRequest,
        LoginRequest,
        SignupRequest,
        SignupVerificationRequest,
    )
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
    from email_verification import (
        confirm_pending_password_reset,
        confirm_pending_signup,
        consume_password_reset_token,
        create_pending_password_reset,
        create_pending_signup,
        generate_verification_code,
        send_verification_email,
    )
    from models import Session, User, UserType
    from schemas import (
        ChangePasswordRequest,
        ForgotPasswordStartRequest,
        ForgotPasswordVerificationRequest,
        LoginRequest,
        SignupRequest,
        SignupVerificationRequest,
    )
    from utils import (
        create_guest_session,
        create_signed_session,
        hash_password,
        set_session_cookie,
        transfer_guest_entries,
        user_payload,
        verify_password,
    )


logger = logging.getLogger(__name__)
router = APIRouter(tags=["authentication"])


def _send_code_or_503(email: str, user_name: str, code: str, purpose: str) -> None:
    try:
        send_verification_email(email, user_name, code, purpose=purpose)
    except RuntimeError as exc:
        logger.error("Email configuration error: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Could not send %s verification email", purpose)
        raise HTTPException(
            status_code=503,
            detail="Could not send the verification email. Check the backend terminal.",
        ) from exc


@router.get("/session/user")
def get_session_user(context=Depends(get_or_create_context)):
    session, user = context
    return user_payload(user, session)


@router.post("/signup")
def signup(
    payload: Union[SignupRequest, SignupVerificationRequest],
    response: Response,
    context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    session, current_user = context
    if current_user.user_type != UserType.GUEST.value:
        raise HTTPException(status_code=400, detail="You are already signed in")

    if isinstance(payload, SignupVerificationRequest):
        pending_signup = confirm_pending_signup(
            payload.challenge_id,
            payload.verification_code,
        )
        if pending_signup is None:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")

        duplicate = db.query(User).filter(
            User.user_id != current_user.user_id,
            or_(
                User.email == pending_signup.email,
                User.user_name == pending_signup.user_name,
            ),
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Username or email is already in use")

        current_user.user_name = pending_signup.user_name
        current_user.email = pending_signup.email
        current_user.hashed_password = pending_signup.hashed_password
        current_user.user_type = UserType.SIGNED.value
        session.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        db.commit()
        db.refresh(current_user)
        set_session_cookie(response, session.session_id)
        result = user_payload(current_user, session)
        result["message"] = "Account verified and created successfully"
        return result

    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    duplicate = db.query(User).filter(
        or_(User.email == payload.email, User.user_name == payload.user_name)
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Username or email is already in use")

    code = generate_verification_code()
    _send_code_or_503(payload.email, payload.user_name, code, purpose="signup")
    challenge_id = create_pending_signup(
        user_name=payload.user_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        code=code,
    )
    return {
        "message": "Verification code sent. Check your inbox.",
        "challenge_id": challenge_id,
        "expires_in_seconds": 300,
    }


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


@router.post("/login/forgot-password")
def forgot_password(
    payload: ForgotPasswordStartRequest,
    _context=Depends(get_or_create_context),
    db: DatabaseSession = Depends(get_db),
):
    user = db.query(User).filter(
        User.email == payload.email,
        User.user_type.in_([UserType.SIGNED.value, UserType.ADMIN.value]),
        User.is_active.is_(True),
    ).first()
    if user is None:
        raise HTTPException(status_code=404, detail="There is no active account using this email address")

    code = generate_verification_code()
    _send_code_or_503(user.email, user.user_name, code, purpose="password_reset")
    challenge_id = create_pending_password_reset(email=user.email, code=code)
    return {
        "message": "Verification code sent. Check your inbox.",
        "challenge_id": challenge_id,
        "expires_in_seconds": 300,
    }


@router.post("/login/forgot-password/verify")
def verify_forgot_password(payload: ForgotPasswordVerificationRequest):
    reset_token = confirm_pending_password_reset(
        payload.challenge_id,
        payload.verification_code,
    )
    if reset_token is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    return {"reset_token": reset_token, "expires_in_seconds": 600}


@router.post("/login/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: DatabaseSession = Depends(get_db),
):
    if payload.new_password != payload.confirm_new_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    email = consume_password_reset_token(payload.reset_token)
    if email is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(
        User.email == email,
        User.user_type.in_([UserType.SIGNED.value, UserType.ADMIN.value]),
        User.is_active.is_(True),
    ).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found or inactive")

    user.hashed_password = hash_password(payload.new_password)
    db.query(Session).filter(
        Session.user_id == user.user_id,
        Session.is_active.is_(True),
    ).update({Session.is_active: False}, synchronize_session=False)
    db.commit()
    return {"message": "Password changed successfully. Log in with your new password."}


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

