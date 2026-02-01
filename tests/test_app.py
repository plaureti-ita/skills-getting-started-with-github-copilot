import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict before/after each test."""
    original = copy.deepcopy(activities)
    yield
    # restore the original mapping
    activities.clear()
    activities.update(original)


def test_get_activities():
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    assert "Basketball Team" in data


def test_signup_success():
    email = "tester@example.com"
    res = client.post("/activities/Basketball%20Team/signup", params={"email": email})
    assert res.status_code == 200
    assert f"Signed up {email}" in res.json().get("message", "")

    # participant now present
    res2 = client.get("/activities")
    assert email in res2.json()["Basketball Team"]["participants"]


def test_signup_already_signed():
    # alex@mergington.edu is already signed for Basketball Team in initial data
    email = "alex@mergington.edu"
    res = client.post("/activities/Basketball%20Team/signup", params={"email": email})
    assert res.status_code == 400


def test_signup_nonexistent_activity():
    res = client.post("/activities/Nonexistent%20Activity/signup", params={"email": "x@y.com"})
    assert res.status_code == 404


def test_unregister_success():
    email = "to-remove@example.com"
    # sign up first
    r1 = client.post("/activities/Chess%20Club/signup", params={"email": email})
    assert r1.status_code == 200

    # now unregister
    r2 = client.post("/activities/Chess%20Club/unregister", params={"email": email})
    assert r2.status_code == 200

    # verify removed
    res = client.get("/activities")
    assert email not in res.json()["Chess Club"]["participants"]


def test_unregister_not_signed():
    res = client.post("/activities/Chess%20Club/unregister", params={"email": "noone@example.com"})
    assert res.status_code == 400
