from threading import Lock
from typing import Optional


_state_lock = Lock()
_active_user_id: Optional[int] = None


def get_active_user_id() -> Optional[int]:
    with _state_lock:
        return _active_user_id


def set_active_user_id(user_id: int) -> None:
    global _active_user_id
    with _state_lock:
        _active_user_id = user_id


def clear_active_user() -> None:
    global _active_user_id
    with _state_lock:
        _active_user_id = None
