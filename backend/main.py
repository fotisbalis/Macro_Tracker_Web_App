from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

try:
    from .archive import router as archive_router
    from .auth import router as auth_router
    from .database import initialize_database
    from .foods import router as foods_router
    from .services.provider import get_ai_provider_name
    from .users import router as users_router
except ImportError:
    from archive import router as archive_router
    from auth import router as auth_router
    from database import initialize_database
    from foods import router as foods_router
    from services.provider import get_ai_provider_name
    from users import router as users_router


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(title="Macro Tracker", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()

app.include_router(auth_router)
app.include_router(foods_router)
app.include_router(archive_router)
app.include_router(users_router)


@app.get("/health")
def health():
    return {"status": "ok", "ai_provider": get_ai_provider_name()}


@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
