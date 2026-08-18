# Macro Tracker

A local macro-tracking web app with:

- a startup chooser for local user profiles;
- separate food logs, archives, and daily targets for every profile;
- no login, password, email verification, cookies, or account sessions;
- an embedded SQLite database (`macro_tracker.db`);
- manual meal entry and optional Qwen-powered macro estimates;
- a vanilla HTML/CSS/JavaScript frontend served by FastAPI.

The mock provider returns intentionally random estimates. Qwen estimates are also approximations and must not be treated as medical or nutritional advice.

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

Copy `.env.example` to `.env`. Keep this setting for local random estimates without API calls:

```dotenv
AI_PROVIDER=mock
```

To use Qwen instead, add your Alibaba Model Studio key:

```dotenv
AI_PROVIDER=qwen
DASHSCOPE_API_KEY=your-private-api-key
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3.5-flash
QWEN_TIMEOUT_SECONDS=30
```

Restart FastAPI after editing `.env`. Never commit the real API key.

The provider contract is in `backend/services/ai_service.py`; implementations are in `backend/services/mock_ai.py` and `backend/services/qwen_ai.py`. Qwen is used only by the AI estimate form. Manual meals and meals copied from the archive do not call the API.
