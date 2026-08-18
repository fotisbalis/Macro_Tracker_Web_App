import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIRECTORY / ".env", override=False)

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

try:
    from .ai_settings import router as ai_settings_router
    from .archive import router as archive_router
    from .database import initialize_database
    from .foods import router as foods_router
    from .profiles import router as profiles_router
    from .services.provider import is_ai_active
    from .users import router as users_router
except ImportError:
    from ai_settings import router as ai_settings_router
    from archive import router as archive_router
    from database import initialize_database
    from foods import router as foods_router
    from profiles import router as profiles_router
    from services.provider import is_ai_active
    from users import router as users_router


RESOURCE_DIRECTORY = Path(getattr(sys, "_MEIPASS", PROJECT_DIRECTORY))
FRONTEND_DIR = RESOURCE_DIRECTORY / "frontend"

app = FastAPI(title="Macro Tracker", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()

app.include_router(ai_settings_router)
app.include_router(profiles_router)
app.include_router(foods_router)
app.include_router(archive_router)
app.include_router(users_router)


@app.get("/health")
def health():
    return {"status": "ok", "ai_provider": "openai", "ai_active": is_ai_active()}


@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
