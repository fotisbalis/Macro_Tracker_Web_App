try:
    from .api_key_store import APIKeyStorageError, load_api_key
    from .openai_ai import OpenAIAIService
except ImportError:
    from services.api_key_store import APIKeyStorageError, load_api_key
    from services.openai_ai import OpenAIAIService


def is_ai_active() -> bool:
    try:
        return bool(load_api_key())
    except APIKeyStorageError:
        return False


ai_service = OpenAIAIService()
