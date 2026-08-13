import os
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:///./test_macro_tracker.db"

from fastapi.testclient import TestClient

from backend import auth
from backend.database import Base, engine
from backend.main import app
from backend.services.ai_service import AIServiceError


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_guest_food_archive_targets_and_delete_flow():
    client = TestClient(app)

    session = client.get("/session/user")
    assert session.status_code == 200
    assert session.json()["user"]["user_type"] == "guest"

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
    assert set(["calories", "protein", "carbs", "fat"]).issubset(entry)

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

    archive = client.get("/archive")
    assert archive.status_code == 200
    assert len(archive.json()["days"]) == 1

    removed = client.delete(f"/foods/{entry['entry_id']}")
    assert removed.status_code == 200
    assert client.get("/days/today").json()["entries"] == []


def test_manual_food_uses_defaults_and_bypasses_ai(monkeypatch):
    async def fail_if_called(_food_name, _quantity):
        raise AssertionError("The AI service must not be called for manual entries")

    monkeypatch.setattr("backend.foods.ai_service.analyze_food", fail_if_called)
    client = TestClient(app)

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
    assert entry["unit"] == "g"
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

    response = client.post("/foods/analyze", json={
        "food_name": "Unavailable estimate",
        "quantity": 100,
    })

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "The AI could not estimate this meal. Please try again or enter the macros manually."
    )
    assert client.get("/days/today").json()["entries"] == []


def test_archived_food_can_be_copied_to_today_without_ai(monkeypatch):
    async def fail_if_called(_food_name, _quantity):
        raise AssertionError("The AI service must not be called when copying an archived meal")

    monkeypatch.setattr("backend.foods.ai_service.analyze_food", fail_if_called)
    client = TestClient(app)
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

    copied_response = client.post(f"/foods/{archived['entry_id']}/add-to-today")
    assert copied_response.status_code == 200
    copied = copied_response.json()["entry"]
    assert copied["entry_id"] != archived["entry_id"]
    assert copied["logged_on"] == date.today().isoformat()
    assert copied["food_name"] == archived["food_name"]
    assert copied["quantity"] == archived["quantity"]
    assert copied["calories"] == archived["calories"]
    assert copied["protein"] == archived["protein"]
    assert copied["carbs"] == archived["carbs"]
    assert copied["fat"] == archived["fat"]
    assert copied["source"] == archived["source"]

    copied_again_response = client.post(f"/foods/{archived['entry_id']}/add-to-today")
    assert copied_again_response.status_code == 200
    copied_again = copied_again_response.json()["entry"]
    assert copied_again["entry_id"] not in {archived["entry_id"], copied["entry_id"]}
    assert copied_again["food_name"] == archived["food_name"]

    cannot_copy_today = client.post(f"/foods/{copied['entry_id']}/add-to-today")
    assert cannot_copy_today.status_code == 400


def test_signup_keeps_guest_entries(monkeypatch):
    sent_code = {}

    def fake_send(_recipient, _user_name, code, purpose="signup"):
        sent_code["code"] = code
        sent_code["purpose"] = purpose

    monkeypatch.setattr(auth, "send_verification_email", fake_send)
    client = TestClient(app)
    client.get("/session/user")
    client.post("/foods/analyze", json={"food_name": "Greek yogurt", "quantity": 200})

    signup_started = client.post("/signup", json={
        "user_name": "macro_user",
        "email": "macro@example.com",
        "password": "strong-pass-123",
        "confirm_password": "strong-pass-123",
    })
    assert signup_started.status_code == 200
    assert sent_code["purpose"] == "signup"

    signup_response = client.post("/signup", json={
        "challenge_id": signup_started.json()["challenge_id"],
        "verification_code": sent_code["code"],
    })
    assert signup_response.status_code == 200
    assert signup_response.json()["user"]["user_type"] == "signed"
    assert len(client.get("/days/today").json()["entries"]) == 1

    logout_response = client.post("/logout")
    assert logout_response.status_code == 200
    assert logout_response.json()["user"]["user_type"] == "guest"

    login_response = client.post("/login", json={
        "email": "macro@example.com",
        "password": "strong-pass-123",
    })
    assert login_response.status_code == 200
    assert login_response.json()["user"]["user_name"] == "macro_user"
    assert len(client.get("/days/today").json()["entries"]) == 1
