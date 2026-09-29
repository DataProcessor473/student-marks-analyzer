"""Pytest fixtures. Uses temp SQLite DB."""
import os
import sys
import tempfile
import pytest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

_test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_test_db.close()
os.environ["DATABASE_URL"] = ""
os.environ["DB_PATH"] = _test_db.name
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-prod"
os.environ["REFRESH_SECRET_KEY"] = "test-refresh-key"
os.environ["DEV_MODE_SMS"] = "true"
os.environ["WEBSOCKET_ENABLED"] = "false"

from fastapi.testclient import TestClient
import main
from main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token(client):
    r = client.post("/auth/login", params={"username": "admin", "password": "Admin@123"})
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": "Bearer " + admin_token}


@pytest.fixture
def sample_student(client, admin_headers):
    payload = {
        "name": "Pytest Student",
        "marks": [85.0, 90.0, 78.0],
        "subjects": ["Math", "Science", "English"],
        "grade": "A",
        "average": 84.33,
        "total_marks": 253.0,
        "timestamp": "2026-01-01T00:00:00",
        "class_name": "PYTEST-A",
    }
    r = client.post("/students/save", json=payload, headers=admin_headers)
    assert r.status_code == 200, f"Create student failed: {r.text}"
    sid = r.json()["id"]
    yield sid
    client.delete(f"/students/delete/{sid}", headers=admin_headers)


def pytest_sessionfinish(session, exitstatus):
    try:
        os.unlink(_test_db.name)
    except Exception:
        pass