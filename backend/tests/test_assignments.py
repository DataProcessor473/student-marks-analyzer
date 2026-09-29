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

def test_submissions_response_has_counts(client, admin_headers, sample_student):
    """The admin cards read total_students / submitted_count / graded_count
    from /assignments/{id}/submissions. If any is missing, the cards show 0."""
    payload = {
        "title": "Counts Test Assignment",
        "description": "For testing summary counts",
        "class_name": "PYTEST-A",
        "subject": "Math",
        "due_date": "2026-12-31",
        "total_marks": 100,
        "recurrence": "none",
    }
    r = client.post("/assignments/create", json=payload, headers=admin_headers)
    assert r.status_code == 200
    aid = r.json()["id"]

    r = client.get(f"/assignments/{aid}/submissions", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()

    assert "submissions" in data
    assert "total_students" in data
    assert "submitted_count" in data
    assert "graded_count" in data

    assert isinstance(data["total_students"], int)
    assert isinstance(data["submitted_count"], int)
    assert isinstance(data["graded_count"], int)

    # Sanity: submitted_count >= graded_count (a graded submission is submitted)
    assert data["submitted_count"] >= data["graded_count"]
    # Sanity: total_students >= submitted_count
    assert data["total_students"] >= data["submitted_count"]
