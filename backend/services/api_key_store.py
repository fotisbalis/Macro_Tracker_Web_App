import ctypes
import os
from ctypes import wintypes
from pathlib import Path
from typing import Optional


APP_DIRECTORY_NAME = "MacroTracker"
KEY_FILE_NAME = "openai-key.bin"
_DPAPI_DESCRIPTION = "Macro Tracker OpenAI API key"
_DPAPI_ENTROPY = b"MacroTracker.OpenAIKey.v1"
_CRYPTPROTECT_UI_FORBIDDEN = 0x01


class APIKeyStorageError(RuntimeError):
    """Raised when the per-user protected API key cannot be accessed."""


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _blob(value: bytes):
    buffer = ctypes.create_string_buffer(value)
    return _DataBlob(
        len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))
    ), buffer


def _key_path() -> Path:
    custom_directory = os.getenv("MACRO_TRACKER_DATA_DIR", "").strip()
    if custom_directory:
        base_directory = Path(custom_directory)
    else:
        local_app_data = os.getenv("LOCALAPPDATA", "").strip()
        if not local_app_data:
            raise APIKeyStorageError("Windows local application data is unavailable.")
        base_directory = Path(local_app_data) / APP_DIRECTORY_NAME
    return base_directory / KEY_FILE_NAME


def _require_windows() -> None:
    if os.name != "nt":
        raise APIKeyStorageError(
            "Protected API key storage is available only in the Windows app."
        )


def _protect(value: bytes) -> bytes:
    _require_windows()
    input_blob, input_buffer = _blob(value)
    entropy_blob, entropy_buffer = _blob(_DPAPI_ENTROPY)
    output_blob = _DataBlob()

    succeeded = ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(input_blob),
        _DPAPI_DESCRIPTION,
        ctypes.byref(entropy_blob),
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )
    # Keep the buffers alive until CryptProtectData returns.
    _ = input_buffer, entropy_buffer
    if not succeeded:
        raise APIKeyStorageError("Windows could not protect the API key.")

    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def _unprotect(value: bytes) -> bytes:
    _require_windows()
    input_blob, input_buffer = _blob(value)
    entropy_blob, entropy_buffer = _blob(_DPAPI_ENTROPY)
    output_blob = _DataBlob()

    succeeded = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        _CRYPTPROTECT_UI_FORBIDDEN,
        ctypes.byref(output_blob),
    )
    _ = input_buffer, entropy_buffer
    if not succeeded:
        raise APIKeyStorageError("Windows could not unlock the saved API key.")

    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output_blob.pbData)


def load_api_key() -> Optional[str]:
    path = _key_path()
    if not path.exists():
        return None
    try:
        api_key = _unprotect(path.read_bytes()).decode("utf-8").strip()
    except (OSError, UnicodeError) as exc:
        raise APIKeyStorageError("The saved API key could not be read.") from exc
    return api_key or None


def save_api_key(api_key: str) -> None:
    normalized_key = api_key.strip()
    if not normalized_key:
        raise ValueError("An OpenAI API key is required.")

    path = _key_path()
    temporary_path = path.with_suffix(".tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path.write_bytes(_protect(normalized_key.encode("utf-8")))
        temporary_path.replace(path)
    except OSError as exc:
        raise APIKeyStorageError("The API key could not be saved.") from exc
    finally:
        if temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                pass


def delete_api_key() -> None:
    path = _key_path()
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise APIKeyStorageError("The saved API key could not be removed.") from exc
