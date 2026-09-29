"""Assignment tests."""


def test_create_assignment(client, admin_headers):
    payload = {
        "title": "Pytest Assignment",
        "description": "Test",
        "class_name": "PYTEST-A",
        "subject": "Math",
        "due_date": "2026-12-31",
        "total_marks": 100,
        "recurrence": "none",
    }
    r = client.post("/assignments/create", json=payload, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["generated"] >= 1


def test_list_assignments(client, admin_headers):
    r = client.get("/assignments", headers=admin_headers)
    assert r.status_code == 200
    assert "assignments" in r.json()


def test_unauthorized_create(client):
    payload = {
        "title": "X", "class_name": "X",
        "due_date": "2026-12-31", "total_marks": 100,
    }
    r = client.post("/assignments/create", json=payload)
    assert r.status_code == 401


def test_recurring_assignment(client, admin_headers):
    payload = {
        "title": "Pytest Weekly",
        "description": "Recurring",
        "class_name": "PYTEST-A",
        "subject": "Math",
        "due_date": "2026-06-01",
        "total_marks": 50,
        "recurrence": "weekly",
        "recurrence_end": "2026-06-22",
    }
    r = client.post("/assignments/create", json=payload, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["generated"] >= 3