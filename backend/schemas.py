from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FoodEntryCreate(BaseModel):
    food_name: str = Field(min_length=2, max_length=140)
    quantity: float = Field(gt=0, le=5000)
    logged_on: Optional[date] = None

    @field_validator("food_name")
    @classmethod
    def normalize_food_name(cls, value: str) -> str:
        return " ".join(value.strip().split())


class SignupRequest(BaseModel):
    user_name: str = Field(min_length=4, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("user_name", "email")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, value: str) -> str:
        normalized = value.lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Enter a valid email address")
        return normalized


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=72)


class TargetUpdate(BaseModel):
    calorie_target: float = Field(gt=0, le=10000)
    protein_target: float = Field(gt=0, le=1000)
    carbs_target: float = Field(gt=0, le=1500)
    fat_target: float = Field(gt=0, le=500)


class MacroResult(BaseModel):
    food_name: str
    quantity: float
    unit: str = "g"
    calories: float = Field(ge=0)
    protein: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fat: float = Field(ge=0)
    source: str = "mock_ai"
