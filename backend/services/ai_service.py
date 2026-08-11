from abc import ABC, abstractmethod

try:
    from ..schemas import MacroResult
except ImportError:
    from schemas import MacroResult


class AIService(ABC):
    """Provider boundary for the mock service and the future real AI."""

    @abstractmethod
    async def analyze_food(self, food_name: str, quantity: float) -> MacroResult:
        raise NotImplementedError

