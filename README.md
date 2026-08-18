# Macro Tracker

A local macro-tracking desktop-web app with:

- an embedded local SQLite database
- manual meal entry and optional ChatGPT-powered macro estimates.
- macro targets, statistics and archive 
- a vanilla HTML/CSS/JavaScript frontend served by FastAPI.

## Windows installer

Got to the releases page and click the latest MacroTracker-Setup-<x.x.x>.exe

## Run locally

From the project root in the VS Code PowerShell terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Then open `http://127.0.0.1:8000`.

SQLite is included with Python, so there is no database server to install. The app creates any missing tables in `macro_tracker.db` on startup. Existing data in that file is preserved. `database.sql` is no longer used.

Opening or refreshing the app always returns to the profile chooser. This does not delete profiles or food data.

## AI configuration

Open the app and select a local profile. When AI is inactive, press **Set up AI**, enter your own OpenAI API key, and press **Save key**. The status changes to **OpenAI active** immediately; the server does not need to restart.

The key is:

- encrypted at rest with Windows Data Protection API (DPAPI);
- stored for the current Windows account under `%LOCALAPPDATA%\MacroTracker`;
- never stored in SQLite, `.env`, browser storage, or the installer;
- removable from the same AI settings dialog.

A user can create or manage keys at `https://platform.openai.com/api-keys`.

`.env` is only needed for optional development settings:

```dotenv
OPENAI_MODEL=gpt-5.6-luna
OPENAI_TIMEOUT_SECONDS=30
```

Restart FastAPI after changing these optional settings. Never put a real API key in `.env` or commit one.

The provider contract is in `backend/services/ai_service.py`, the OpenAI implementation is in `backend/services/openai_ai.py`, and protected key storage is in `backend/services/api_key_store.py`. OpenAI is used only by the AI estimate form. Manual meals and meals copied from the archive do not call the API.
