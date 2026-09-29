"""Student CRUD tests."""


def test_list_students(client, admin_headers):
    r = client.get("/students", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "count" in data
    assert "students" in data


def test_create_and_fetch(client, admin_headers, sample_student):
    r = client.get(f"/students/{sample_student}", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == sample_student
    assert data["name"] == "Pytest Student"


def test_student_profile(client, admin_headers, sample_student):
    r = client.get(f"/students/{sample_student}/profile", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "student" in data
    assert "attendance" in data
    assert "trends" in data


def test_delete_student(client, admin_headers):
    payload = {
        "name": "To Be Deleted",
        "marks": [70.0], "subjects": ["Test"],
        "grade": "C", "average": 70.0, "total_marks": 70.0,
        "timestamp": "2026-01-01T00:00:00", "class_name": "PYTEST-DELETE",
    }
    r = client.post("/students/save", json=payload, headers=admin_headers)
    assert r.status_code == 200
    sid = r.json()["id"]
    r = client.delete(f"/students/delete/{sid}", headers=admin_headers)
    assert r.status_code == 200
    r = client.get(f"/students/{sid}", headers=admin_headers)
    assert r.status_code == 404


def test_unauthorized(client):
    r = client.get("/students")
    assert r.status_code == 401


def test_stats_overall(client, admin_headers):
    r = client.get("/stats/overall", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_students" in data or "message" in data


def test_analytics_dashboard(client, admin_headers):
    r = client.get("/analytics/dashboard", headers=admin_headers)
    assert r.status_code == 200
    assert "has_data" in r.json()