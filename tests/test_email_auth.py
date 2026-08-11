import os

os.environ["DATABASE_URL"] = "sqlite:///./test_email_auth.db"

from fastapi import Response

from backend import auth
from backend.database import Base, SessionLocal, engine
from backend.models import Session, User
from backend.schemas import (
    ChangePasswordRequest,
    ForgotPasswordStartRequest,
    ForgotPasswordVerificationRequest,
    SignupRequest,
    SignupVerificationRequest,
)
from backend.utils import create_guest_session, verify_password


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_signup_verification_and_password_reset(monkeypatch=None):
    sent_codes = []

    def fake_send(recipient, user_name, code, purpose="signup"):
        sent_codes.append({"recipient": recipient, "code": code, "purpose": purpose})

    original_sender = auth.send_verification_email
    auth.send_verification_email = fake_send
    db = SessionLocal()
    try:
        response = Response()
        session, guest = create_guest_session(db, response)
        context = (session, guest)

        started = auth.signup(
            SignupRequest(
                user_name="verified_user",
                email="verified@example.com",
                password="initial-password",
                confirm_password="initial-password",
            ),
            response,
            context,
            db,
        )
        assert started["challenge_id"]
        assert sent_codes[-1]["purpose"] == "signup"

        completed = auth.signup(
            SignupVerificationRequest(
                challenge_id=started["challenge_id"],
                verification_code=sent_codes[-1]["code"],
            ),
            response,
            context,
            db,
        )
        assert completed["user"]["user_type"] == "signed"

        reset_started = auth.forgot_password(
            ForgotPasswordStartRequest(email="verified@example.com"),
            context,
            db,
        )
        assert sent_codes[-1]["purpose"] == "password_reset"

        reset_verified = auth.verify_forgot_password(
            ForgotPasswordVerificationRequest(
                challenge_id=reset_started["challenge_id"],
                verification_code=sent_codes[-1]["code"],
            )
        )
        changed = auth.change_password(
            ChangePasswordRequest(
                reset_token=reset_verified["reset_token"],
                new_password="replacement-password",
                confirm_new_password="replacement-password",
            ),
            db,
        )
        assert "successfully" in changed["message"]

        user = db.query(User).filter(User.email == "verified@example.com").one()
        assert verify_password("replacement-password", user.hashed_password)
        active_sessions = db.query(Session).filter(
            Session.user_id == user.user_id,
            Session.is_active.is_(True),
        ).count()
        assert active_sessions == 0
    finally:
        auth.send_verification_email = original_sender
        db.close()

