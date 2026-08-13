import os

try:
    from .ai_service import AIService
    from .mock_ai import MockAIService
except ImportError:
    from services.ai_service import AIService
    from services.mock_ai import MockAIService


def get_ai_provider_name() -> str:
    return os.getenv("AI_PROVIDER", "mock").strip().lower() or "mock"


def create_ai_service() -> AIService:
    provider = get_ai_provider_name()
    if provider == "mock":
        return MockAIService()
    if provider == "qwen":
        try:
            from .qwen_ai import QwenAIService
        except ImportError:
            from services.qwen_ai import QwenAIService
        return QwenAIService()
    raise RuntimeError(f"Unsupported AI_PROVIDER: {provider}")


ai_service = create_ai_service()
