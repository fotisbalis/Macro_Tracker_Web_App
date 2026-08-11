from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Identity, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

try:
    from .database import Base
except ImportError:
    from database import Base


class UserType(str, Enum):
    GUEST = "guest"
    ADMIN = "admin"
    SIGNED = "signed"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, index=True)
    user_name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    user_type: Mapped[str] = mapped_column(String(20), default=UserType.GUEST.value, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    calorie_target: Mapped[float] = mapped_column(Float, default=2500.0, nullable=False)
    protein_target: Mapped[float] = mapped_column(Float, default=180.0, nullable=False)
    carbs_target: Mapped[float] = mapped_column(Float, default=280.0, nullable=False)
    fat_target: Mapped[float] = mapped_column(Float, default=75.0, nullable=False)


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class FoodEntry(Base):
    __tablename__ = "food_entries"

    entry_id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sessions.session_id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    food_name: Mapped[str] = mapped_column(String(140), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="g", nullable=False)
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein: Mapped[float] = mapped_column(Float, nullable=False)
    carbs: Mapped[float] = mapped_column(Float, nullable=False)
    fat: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(40), default="mock_ai", nullable=False)
    logged_on: Mapped[date] = mapped_column(Date, default=date.today, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
