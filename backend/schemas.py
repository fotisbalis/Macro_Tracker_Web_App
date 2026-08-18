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


class ManualFoodEntryCreate(BaseModel):
    food_name: Optional[str] = Field(default=None, max_length=140)
    quantity: Optional[float] = Field(default=0, ge=0, le=5000)
    calories: float = Field(ge=0)
    protein: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fat: float = Field(ge=0)
    logged_on: Optional[date] = None

    @field_validator("food_name")
    @classmethod
    def normalize_optional_food_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None


class ProfileCreate(BaseModel):
    user_name: str = Field(min_length=1, max_length=80)

    @field_validator("user_name")
    @classmethod
    def normalize_user_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("User name cannot be empty")
        return normalized


class ProfileSelect(BaseModel):
    user_id: int = Field(gt=0)


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
