import os

os.environ["DATABASE_URL"] = "sqlite:///./test_macro_tracker.db"

from fastapi.testclient import TestClient

from backend import auth
from backend.database import Base, engine
from backend.main import app


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
