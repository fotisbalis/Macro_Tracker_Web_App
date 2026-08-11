# Macro Tracker MVP

- vanilla HTML, CSS, and modular JavaScript frontend;
- FastAPI route modules;
- SQLAlchemy persistence;
- cookie-based guest and signed-user sessions;
- Home, Archive, and User pages;
- replaceable AI service boundary.

The current `MockAIService` returns intentionally random macro estimates. These values are placeholders and must not be treated as nutrition advice.

## Run locally

Create a virtual environment, install `requirements.txt`, and run from the project root:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Then open `http://127.0.0.1:8000`.

For the same PostgreSQL setup used by the Waste Detector, copy `.env.example` to `.env`, replace `YOUR_PASSWORD`, and adjust the database name if needed. SQLite remains the zero-configuration fallback when `DATABASE_URL` is not set.

## Replace the mock AI

The provider contract is in `backend/services/ai_service.py`, and the temporary implementation is in `backend/services/mock_ai.py`. A real provider only needs to return the validated `MacroResult` structure:

```json
{
  "food_name": "chicken breast",
  "quantity": 250,
  "unit": "g",
  "calories": 412.5,
  "protein": 77.5,
  "carbs": 0,
  "fat": 9,
  "source": "provider_name"
}
```
