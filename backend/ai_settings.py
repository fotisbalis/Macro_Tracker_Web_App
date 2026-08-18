from fastapi import APIRouter, HTTPException, status

try:
    from .schemas import APIKeyUpdate
    from .services.api_key_store import (
        APIKeyStorageError,
        delete_api_key,
        load_api_key,
        save_api_key,
    )
    from .services.openai_ai import DEFAULT_MODEL
except ImportError:
    from schemas import APIKeyUpdate
    from services.api_key_store import (
        APIKeyStorageError,
        delete_api_key,
        load_api_key,
        save_api_key,
    )
    from services.openai_ai import DEFAULT_MODEL


router = APIRouter(prefix="/ai", tags=["AI settings"])


@router.get("/status")
def ai_status():
    try:
        active = bool(load_api_key())
    except APIKeyStorageError:
        return {
            "active": False,
            "storage_available": False,
            "model": DEFAULT_MODEL,
        }
    return {
        "active": active,
        "storage_available": True,
        "model": DEFAULT_MODEL,
    }


@router.put("/api-key")
def update_api_key(payload: APIKeyUpdate):
    try:
        save_api_key(payload.api_key.get_secret_value())
    except (APIKeyStorageError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Windows could not save the API key securely.",
        ) from exc
    return {"message": "OpenAI API key saved securely for this Windows user."}


@router.delete("/api-key")
def remove_api_key():
    try:
        delete_api_key()
    except APIKeyStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Windows could not remove the saved API key.",
        ) from exc
    return {"message": "OpenAI API key removed. AI is now inactive."}
