import hashlib
import hmac
import os
import secrets
import smtplib
import ssl
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from threading import Lock
from typing import Optional


VERIFICATION_CODE_LIFETIME = timedelta(minutes=5)
PASSWORD_RESET_TOKEN_LIFETIME = timedelta(minutes=10)
MAX_VERIFICATION_ATTEMPTS = 5


@dataclass
class PendingSignup:
    user_name: str
    email: str
    hashed_password: str
    code_hash: str
    expires_at: datetime
    attempts: int = 0


@dataclass
class PendingPasswordReset:
    email: str
    code_hash: str
    expires_at: datetime
    attempts: int = 0


@dataclass
class PasswordResetToken:
    email: str
    expires_at: datetime


pending_signups = {}
pending_password_resets = {}
password_reset_tokens = {}
pending_signups_lock = Lock()
password_resets_lock = Lock()


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _remove_expired(items: dict, now: datetime) -> None:
    expired_keys = [key for key, value in items.items() if value.expires_at <= now]
    for key in expired_keys:
        del items[key]


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def send_verification_email(
    recipient: str,
    user_name: str,
    code: str,
    purpose: str = "signup",
) -> None:
    settings = {
        "SMTP_HOST": os.getenv("SMTP_HOST"),
        "SMTP_PORT": os.getenv("SMTP_PORT"),
        "SMTP_USERNAME": os.getenv("SMTP_USERNAME"),
        "SMTP_PASSWORD": os.getenv("SMTP_PASSWORD"),
        "EMAIL_FROM": os.getenv("EMAIL_FROM"),
    }
    missing = [name for name, value in settings.items() if not value]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    try:
        port = int(settings["SMTP_PORT"])
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT must be a number") from exc

    is_password_reset = purpose == "password_reset"
    action = "reset your password" if is_password_reset else "finish creating your account"
    subject = "Reset your Macro Tracker password" if is_password_reset else "Verify your Macro Tracker account"
    minutes = int(VERIFICATION_CODE_LIFETIME.total_seconds() // 60)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings["EMAIL_FROM"]
    message["To"] = recipient
    message.set_content(
        f"""Hello {user_name},

Use this verification code to {action}:

{code}

The code expires in {minutes} minutes.
If you have any questions, feel free to reply to this email.
"""
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(settings["SMTP_HOST"], port, timeout=15) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(settings["SMTP_USERNAME"], settings["SMTP_PASSWORD"])
        server.send_message(message)


def create_pending_signup(user_name: str, email: str, hashed_password: str, code: str) -> str:
    now = datetime.now(timezone.utc)
    challenge_id = secrets.token_urlsafe(32)
    with pending_signups_lock:
        _remove_expired(pending_signups, now)
        pending_signups[challenge_id] = PendingSignup(
            user_name=user_name,
            email=email,
            hashed_password=hashed_password,
            code_hash=_hash_code(code),
            expires_at=now + VERIFICATION_CODE_LIFETIME,
        )
    return challenge_id


def confirm_pending_signup(challenge_id: str, verification_code: str) -> Optional[PendingSignup]:
    now = datetime.now(timezone.utc)
    with pending_signups_lock:
        pending_signup = pending_signups.get(challenge_id)
        if pending_signup is None or pending_signup.expires_at <= now:
            pending_signups.pop(challenge_id, None)
            return None
        if not hmac.compare_digest(pending_signup.code_hash, _hash_code(verification_code)):
            pending_signup.attempts += 1
            if pending_signup.attempts >= MAX_VERIFICATION_ATTEMPTS:
                del pending_signups[challenge_id]
            return None
        del pending_signups[challenge_id]
        return pending_signup


def create_pending_password_reset(email: str, code: str) -> str:
    now = datetime.now(timezone.utc)
    challenge_id = secrets.token_urlsafe(32)
    with password_resets_lock:
        _remove_expired(pending_password_resets, now)
        _remove_expired(password_reset_tokens, now)
        pending_password_resets[challenge_id] = PendingPasswordReset(
            email=email,
            code_hash=_hash_code(code),
            expires_at=now + VERIFICATION_CODE_LIFETIME,
        )
    return challenge_id


def confirm_pending_password_reset(challenge_id: str, verification_code: str) -> Optional[str]:
    now = datetime.now(timezone.utc)
    with password_resets_lock:
        pending_reset = pending_password_resets.get(challenge_id)
        if pending_reset is None or pending_reset.expires_at <= now:
            pending_password_resets.pop(challenge_id, None)
            return None
        if not hmac.compare_digest(pending_reset.code_hash, _hash_code(verification_code)):
            pending_reset.attempts += 1
            if pending_reset.attempts >= MAX_VERIFICATION_ATTEMPTS:
                del pending_password_resets[challenge_id]
            return None

        del pending_password_resets[challenge_id]
        token = secrets.token_urlsafe(32)
        password_reset_tokens[token] = PasswordResetToken(
            email=pending_reset.email,
            expires_at=now + PASSWORD_RESET_TOKEN_LIFETIME,
        )
        return token


def consume_password_reset_token(token: str) -> Optional[str]:
    now = datetime.now(timezone.utc)
    with password_resets_lock:
        reset_token = password_reset_tokens.get(token)
        if reset_token is None or reset_token.expires_at <= now:
            password_reset_tokens.pop(token, None)
            return None
        del password_reset_tokens[token]
        return reset_token.email

