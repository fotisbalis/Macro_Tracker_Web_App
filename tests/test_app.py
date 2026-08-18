import os
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:///./test_macro_tracker.db"
os.environ["AI_PROVIDER"] = "mock"

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from backend.database import Base, engine
from backend.main import app
from backend.profile_state import clear_active_user
from backend.services.ai_service import AIServiceError


def setup_function():
    clear_active_user()
    Base.metadata.drop_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS sessions"))
    Base.metadata.create_all(bind=engine)


def create_profile(client: TestClient, name: str = "Fotis") -> dict:
    response = client.post("/profiles", json={"user_name": name})
    assert response.status_code == 200
    return response.json()["user"]


def test_profiles_are_required_and_can_be_created_and_selected():
    client = TestClient(app)

    assert client.get("/profiles/current").json() == {"user": None}
    assert client.get("/days/today").status_code == 409

    user = create_profile(client, "  Fotis   Local  ")
    assert user["user_name"] == "Fotis Local"
    assert set(user) == {"user_id", "user_name", "is_active", "targets"}
    assert client.get("/profiles/current").json()["user"]["user_id"] == user["user_id"]
    assert client.get("/profiles").json()["users"] == [user]

    duplicate = client.post("/profiles", json={"user_name": "fotis local"})
    assert duplicate.status_code == 409
    assert client.post("/profiles", json={"user_name": "   "}).status_code == 422

    assert client.post("/profiles/deselect").status_code == 200
    assert client.get("/profiles/current").json() == {"user": None}
    selected = client.post("/profiles/select", json={"user_id": user["user_id"]})
    assert selected.status_code == 200
    assert selected.json()["user"]["user_name"] == "Fotis Local"

    api_paths = app.openapi()["paths"]
    assert "/login" not in api_paths
    assert "/signup" not in api_paths
    assert "/forgot-password" not in api_paths
    assert "/logout" not in api_paths


def test_food_logs_and_targets_are_isolated_by_profile():
    client = TestClient(app)
    first = create_profile(client, "First user")
    first_entry = client.post("/foods/manual", json={
        "food_name": "First meal",
        "quantity": 100,
        "calories": 300,
        "protein": 20,
        "carbs": 30,
        "fat": 10,
    })
    assert first_entry.status_code == 200

    second = create_profile(client, "Second user")
    assert client.get("/days/today").json()["entries"] == []
    updated = client.patch("/users/me/targets", json={
        "calorie_target": 2000,
        "protein_target": 150,
        "carbs_target": 220,
        "fat_target": 65,
    })
    assert updated.status_code == 200

    selected = client.post("/profiles/select", json={"user_id": first["user_id"]})
    assert selected.status_code == 200
    assert len(client.get("/days/today").json()["entries"]) == 1
    assert selected.json()["user"]["targets"]["calories"] == 2500

    selected_second = client.post("/profiles/select", json={"user_id": second["user_id"]})
    assert selected_second.json()["user"]["targets"]["calories"] == 2000


def test_food_archive_targets_and_delete_flow():
    client = TestClient(app)
    create_profile(client)

    empty_day = client.get("/days/today")
    assert empty_day.status_code == 200
    assert empty_day.json()["entries"] == []

    added = client.post("/foods/analyze", json={"food_name": "Chicken breast", "quantity": 250})
    assert added.status_code == 200
    entry = added.json()["entry"]
    assert entry["food_name"] == "Chicken breast"
    assert entry["quantity"] == 250
    assert entry["unit"] == "g"
    assert entry["source"] == "mock_ai"
    assert {"calories", "protein", "carbs", "fat"}.issubset(entry)

    today = client.get("/days/today").json()
    assert len(today["entries"]) == 1
    assert today["totals"]["calories"] == entry["calories"]

    targets = client.patch("/users/me/targets", json={
        "calorie_target": 2200,
        "protein_target": 170,
        "carbs_target": 230,
        "fat_target": 70,
    })
    assert targets.status_code == 200
    assert targets.json()["targets"]["calories"] == 2200

    assert len(client.get("/archive").json()["days"]) == 1
    assert client.delete(f"/foods/{entry['entry_id']}").status_code == 200
    assert client.get("/days/today").json()["entries"] == []


def test_manual_food_uses_defaults_and_bypasses_ai(monkeypatch):
    async def fail_if_called(_food_name, _quantity):
        raise AssertionError("The AI service must not be called for manual entries")

    monkeypatch.setattr("backend.foods.ai_service.analyze_food", fail_if_called)
    client = TestClient(app)
    create_profile(client)

    added = client.post("/foods/manual", json={
        "food_name": "",
        "calories": 640,
        "protein": 42.5,
        "carbs": 71,
        "fat": 18.2,
    })

    assert added.status_code == 200
    entry = added.json()["entry"]
    assert entry["food_name"].startswith("manual_meal_")
    assert entry["quantity"] == 0
    assert entry["source"] == "manual"
    assert entry["calories"] == 640
    assert entry["protein"] == 42.5
    assert entry["carbs"] == 71
    assert entry["fat"] == 18.2


def test_ai_provider_failure_is_safe_and_does_not_save_entry(monkeypatch):
    async def fail_estimate(_food_name, _quantity):
        raise AIServiceError("private provider details")

    monkeypatch.setattr("backend.foods.ai_service.analyze_food", fail_estimate)
    client = TestClient(app)
    create_profile(client)

    response = client.post("/foods/analyze", json={
        "food_name": "Unavailable estimate",
        "quantity": 100,
    })

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The AI could not estimate this meal. Please try again or enter the macros manually."
    )
    assert client.get("/days/today").json()["entries"] == []


def test_archived_food_can_be_copied_to_today_multiple_times_without_ai(monkeypatch):
    async def fail_if_called(_food_name, _quantity):
        raise AssertionError("The AI service must not be called when copying an archived meal")

    monkeypatch.setattr("backend.foods.ai_service.analyze_food", fail_if_called)
    client = TestClient(app)
    create_profile(client)
    previous_day = (date.today() - timedelta(days=1)).isoformat()
    archived = client.post("/foods/manual", json={
        "food_name": "Yesterday's pasta",
        "quantity": 350,
        "calories": 720,
        "protein": 28,
        "carbs": 112,
        "fat": 18,
        "logged_on": previous_day,
    }).json()["entry"]

    copied = client.post(f"/foods/{archived['entry_id']}/add-to-today").json()["entry"]
    copied_again_response = client.post(f"/foods/{archived['entry_id']}/add-to-today")
    assert copied_again_response.status_code == 200
    copied_again = copied_again_response.json()["entry"]
    assert copied_again["entry_id"] not in {archived["entry_id"], copied["entry_id"]}
    assert copied_again["food_name"] == archived["food_name"]
    assert client.post(f"/foods/{copied['entry_id']}/add-to-today").status_code == 400


def test_sqlite_schema_contains_no_authentication_or_session_fields():
    schema = inspect(engine)
    assert set(schema.get_table_names()) == {"food_entries", "users"}
    user_columns = {column["name"] for column in schema.get_columns("users")}
    food_columns = {column["name"] for column in schema.get_columns("food_entries")}
    assert {"email", "hashed_password", "user_type"}.isdisjoint(user_columns)
    assert "session_id" not in food_columns
