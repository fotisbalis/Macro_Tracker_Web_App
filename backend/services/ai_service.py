from abc import ABC, abstractmethod
from typing import Optional

try:
    from ..schemas import MacroResult
except ImportError:
    from schemas import MacroResult


class AIService(ABC):
    """Provider boundary for AI macro estimates."""

    @abstractmethod
    async def analyze_food(self, food_name: str, quantity: Optional[float]) -> MacroResult:
        raise NotImplementedError


class AIServiceError(RuntimeError):
    """A safe, provider-independent error raised when an estimate cannot be made."""


class AIInactiveError(AIServiceError):
    """Raised when the user has not configured an OpenAI API key."""
