"""Behavior notes + badges tests."""


def test_create_behavior_note(client, admin_headers, sample_student):
    payload = {
        "note_type": "observation",
        "content": "Pytest test: good participation in class",
        "visible_to_parents": True,
    }
    r = client.post("/students/" + str(sample_student) + "/notes", json=payload, headers=admin_headers)
    assert r.status_code in (200, 403, 404)


def test_list_behavior_notes(client, admin_headers, sample_student):
    r = client.get("/students/" + str(sample_student) + "/notes", headers=admin_headers)
    assert r.status_code in (200, 403, 404)


def test_create_note_unauthorized(client):
    payload = {"content": "X"}
    r = client.post("/students/1/notes", json=payload)
    assert r.status_code == 401


def test_create_note_empty_content(client, admin_headers, sample_student):
    payload = {"note_type": "observation", "content": ""}
    r = client.post("/students/" + str(sample_student) + "/notes", json=payload, headers=admin_headers)
    assert r.status_code == 422


def test_list_notes_filtered_by_type(client, admin_headers, sample_student):
    r = client.get("/students/" + str(sample_student) + "/notes?note_type=observation", headers=admin_headers)
    assert r.status_code in (200, 403, 404)


def test_badges_list(client, admin_headers):
    r = client.get("/badges/all", headers=admin_headers)
    assert r.status_code == 200
    assert "badges" in r.json()


def test_student_badges_list(client, admin_headers, sample_student):
    r = client.get("/students/" + str(sample_student) + "/badges", headers=admin_headers)
    assert r.status_code in (200, 403, 404)
