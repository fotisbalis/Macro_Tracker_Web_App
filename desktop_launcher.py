"""Windows desktop entry point for the packaged Macro Tracker app."""

import os
import socket
import threading
import time
from pathlib import Path

import uvicorn
import webview


APP_DATA_DIRECTORY = Path(os.environ["LOCALAPPDATA"]) / "MacroTracker"
APP_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{(APP_DATA_DIRECTORY / 'macro_tracker.db').as_posix()}",
)

from backend.main import app


def get_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main() -> None:
    port = get_available_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    )
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("Macro Tracker could not start its local server.")

    webview.create_window("Macro Tracker", f"http://127.0.0.1:{port}")
    webview.start()

    server.should_exit = True
    server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
