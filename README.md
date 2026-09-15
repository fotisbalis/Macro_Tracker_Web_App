# Macro Tracker

A local macro-tracking desktop-web app with:

- an embedded local SQLite database
- manual meal entry and optional ChatGPT-powered macro estimates.
- macro targets, statistics and archive 
- a date-selectable diary and per-profile favorite foods
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

## Diary dates and favorites

On Home, choose a **Diary date** to view that day's foods and totals. Manual and AI entries are saved to the selected date. Use **Today** to return to the current day; future dates are not accepted.

Dates throughout the app use **DD/MM/YYYY**. Type a date in that format or use the calendar button on Home, Favorites, and the Statistics custom range.

Each food in the Home log has a **Quantity** field, **− / +** controls, and an **Update** button. Weighed foods accept 0.1 to 5,000 g, with 1 g per click. Foods without a recorded weight start at **1 portion** and use whole-number counts (1, 2, 3, …), with one portion per click. Updating the quantity scales that entry's macros and refreshes the daily totals, including on previous days. Saved favorites are unaffected.

Press **☆ Save** beside a food in the diary or archive to save its portion and macros. Open **Favorites** in the navigation, choose a date, and press **Add to selected day** to log that saved portion without calling AI. Favorites are separate for each profile, survive deletion of the original diary entry, and can be removed without changing food history. Saving an identical food again reuses the existing favorite.

For favorites with a saved weight, change **Weight to add** to preview proportionally scaled calories and macros before logging. Favorites without a recorded weight use **Quantity to add** for a whole-number portion count. This changes only the new diary entry; the original favorite keeps its saved portion. Older foods stored without a weight are also treated as one portion.

The favorites table is created automatically on backend startup, preserving existing profiles and food entries.

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
