import random

try:
    from ..schemas import MacroResult
    from .ai_service import AIService
except ImportError:
    from schemas import MacroResult
    from services.ai_service import AIService


class MockAIService(AIService):
    async def analyze_food(self, food_name: str, quantity: float) -> MacroResult:
        scale = quantity / 100.0
        protein_per_100g = random.uniform(2, 32)
        carbs_per_100g = random.uniform(1, 55)
        fat_per_100g = random.uniform(1, 24)

        protein = protein_per_100g * scale
        carbs = carbs_per_100g * scale
        fat = fat_per_100g * scale
        calories = protein * 4 + carbs * 4 + fat * 9

        return MacroResult(
            food_name=food_name,
            quantity=quantity,
            unit="g",
            calories=round(calories, 1),
            protein=round(protein, 1),
            carbs=round(carbs, 1),
            fat=round(fat, 1),
            source="mock_ai",
        )
