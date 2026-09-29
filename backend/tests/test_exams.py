"""Exam endpoint tests."""


def test_create_exam(client, admin_headers):
    payload = {
        "name": "Pytest Midterm",
        "class_name": "PYTEST-A",
        "subject": "Math",
        "exam_date": "2026-06-15",
        "start_time": "09:00",
        "end_time": "11:00",
        "total_marks": 100,
        "room": "A-101",
        "notes": "pytest test",
    }
    r = client.post("/exams/create", json=payload, headers=admin_headers)
    assert r.status_code == 200


def test_list_exams(client, admin_headers):
    r = client.get("/exams", headers=admin_headers)
    assert r.status_code == 200
    assert "exams" in r.json()


def test_list_exams_filtered_by_class(client, admin_headers):
    r = client.get("/exams?class_name=PYTEST-A", headers=admin_headers)
    assert r.status_code == 200


def test_create_exam_unauthorized(client):
    payload = {"name": "X", "exam_date": "2026-06-15"}
    r = client.post("/exams/create", json=payload)
    assert r.status_code == 401


def test_create_exam_missing_fields(client, admin_headers):
    r = client.post("/exams/create", json={}, headers=admin_headers)
    assert r.status_code == 422


def test_delete_nonexistent_exam(client, admin_headers):
    r = client.delete("/exams/99999999", headers=admin_headers)
    assert r.status_code in (200, 404)
