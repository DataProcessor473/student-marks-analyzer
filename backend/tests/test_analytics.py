"""Analytics + ML tests."""


def test_analyze_basic(client, admin_headers):
    payload = {
        "marks": [85.0, 90.0, 78.0, 92.0],
        "student_name": "Pytest Analyzer",
        "subject_names": ["Math", "Science", "English", "History"],
        "passing_threshold": 40,
        "grade_scheme": "standard",
    }
    r = client.post("/analyze", json=payload, headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["student_name"] == "Pytest Analyzer"
    assert data["average"] == 86.25
    assert data["grade"] in ["A+", "A", "B", "C", "D", "E", "F"]
    assert "recommendations" in data


def test_analyze_empty_marks(client, admin_headers):
    r = client.post("/analyze", json={"marks": [], "student_name": "X"}, headers=admin_headers)
    assert r.status_code == 422


def test_analyze_out_of_range(client, admin_headers):
    r = client.post("/analyze", json={"marks": [150.0], "student_name": "X"}, headers=admin_headers)
    assert r.status_code == 422


def test_ml_status(client, admin_headers):
    r = client.get("/ml/status", headers=admin_headers)
    assert r.status_code == 200
    assert "available" in r.json()


def test_grade_schemes_list(client, admin_headers):
    r = client.get("/grade-schemes", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json().get("schemes"), list)


def test_badges_list(client, admin_headers):
    r = client.get("/badges/all", headers=admin_headers)
    assert r.status_code == 200
    assert isinstance(r.json().get("badges"), list)