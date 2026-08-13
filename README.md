# Macro Tracker MVP

- vanilla HTML, CSS, and modular JavaScript frontend;
- FastAPI route modules;
- SQLAlchemy persistence;
- cookie-based guest and signed-user sessions;
- Home, Archive, and User pages;
- manual meal entry that bypasses the AI provider;
- selectable mock or Qwen AI service behind one provider boundary.

The default `MockAIService` returns intentionally random macro estimates. These values are placeholders and must not be treated as nutrition advice. Qwen estimates are also approximations, not medical advice.

## Run locally

Create a virtual environment, install `requirements.txt`, and run from the project root:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Then open `http://127.0.0.1:8000`.

For the same PostgreSQL setup used by the Waste Detector, copy `.env.example` to `.env`, replace `YOUR_PASSWORD`, and adjust the database name if needed. SQLite remains the zero-configuration fallback when `DATABASE_URL` is not set.

Signup and password-reset verification use the SMTP settings in `.env`. Codes expire after five minutes and are stored in memory for this local version, so restarting the backend invalidates outstanding codes.

## Enable Qwen

The Qwen integration uses Alibaba Model Studio's OpenAI-compatible Chat Completions API. In `.env`, add your private key and switch the provider:

```dotenv
AI_PROVIDER=qwen
DASHSCOPE_API_KEY=your-private-api-key
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen3.5-flash
QWEN_TIMEOUT_SECONDS=30
```

Restart FastAPI after changing `.env`. Set `AI_PROVIDER=mock` whenever you want local random estimates without API calls. Never place the real key in `.env.example`, source code, or Git.

The provider contract is in `backend/services/ai_service.py`; implementations are in `backend/services/mock_ai.py` and `backend/services/qwen_ai.py`. Every provider returns the validated `MacroResult` structure:

```json
{
  "food_name": "chicken breast",
  "quantity": 250,
  "unit": "g",
  "calories": 412.5,
  "protein": 77.5,
  "carbs": 0,
  "fat": 9,
  "source": "qwen:qwen3.5-flash"
}
```

Qwen is called only by the AI estimate form. Manual meals and copies from the archive do not call the API.
