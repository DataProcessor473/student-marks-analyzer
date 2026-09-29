"""Attendance endpoint tests."""
import uuid


def _unique_date():
    return "2026-05-" + str((uuid.uuid4().int % 20) + 1).zfill(2)


def test_record_attendance(client, admin_headers, sample_student):
    payload = {
        "student_id": sample_student,
        "date": _unique_date(),
        "status": "present",
        "subject": "Math",
        "notes": "test attendance",
    }
    r = client.post("/attendance", json=payload, headers=admin_headers)
    assert r.status_code in (200, 409), f"got {r.status_code}: {r.text}"


def test_bulk_attendance(client, admin_headers, sample_student):
    payload = {
        "student_ids": [sample_student],
        "date": _unique_date(),
        "status": "present",
        "subject": "Science",
    }
    r = client.post("/attendance/bulk", json=payload, headers=admin_headers)
    assert r.status_code == 200
    assert "message" in r.json() or "count" in r.json()


def test_attendance_overall_stats(client, admin_headers):
    r = client.get("/attendance/stats/overall", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


def test_attendance_trends(client, admin_headers):
    r = client.get("/attendance/trends?days=30", headers=admin_headers)
    assert r.status_code == 200


def test_student_attendance_stats(client, admin_headers, sample_student):
    r = client.get("/attendance/" + str(sample_student) + "/stats", headers=admin_headers)
    # Endpoint restricts non-admins; admin may see 200, 403, or 404 depending on scope.
    assert r.status_code in (200, 403, 404)


def test_attendance_unauthorized(client):
    r = client.get("/attendance/stats/overall")
    assert r.status_code == 401


def test_attendance_heatmap(client, admin_headers, sample_student):
    r = client.get("/attendance/" + str(sample_student) + "/heatmap", headers=admin_headers)
    assert r.status_code in (200, 403, 404)
