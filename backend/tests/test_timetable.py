"""Timetable endpoint tests."""


def test_create_timetable_entry(client, admin_headers):
    payload = {
        "class_name": "PYTEST-A",
        "day_of_week": "Monday",
        "period": 1,
        "subject": "Math",
        "teacher_name": "Mr. Pytest",
        "room": "A-101",
        "start_time": "09:00",
        "end_time": "10:00",
    }
    r = client.post("/timetable/create", json=payload, headers=admin_headers)
    assert r.status_code in (200, 409)


def test_list_timetable(client, admin_headers):
    r = client.get("/timetable", headers=admin_headers)
    assert r.status_code == 200


def test_list_timetable_filtered_by_class(client, admin_headers):
    r = client.get("/timetable?class_name=PYTEST-A", headers=admin_headers)
    assert r.status_code == 200


def test_timetable_unauthorized(client):
    r = client.get("/timetable")
    assert r.status_code == 401


def test_create_timetable_missing_fields(client, admin_headers):
    r = client.post("/timetable/create", json={}, headers=admin_headers)
    assert r.status_code == 422


def test_delete_nonexistent_timetable(client, admin_headers):
    r = client.delete("/timetable/99999999", headers=admin_headers)
    assert r.status_code in (200, 404)
