"""Auth endpoint tests."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "version" in data
    assert "features" in data


def test_login_success(client):
    r = client.post("/auth/login", params={"username": "admin", "password": "Admin@123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_login_invalid_password(client):
    r = client.post("/auth/login", params={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/auth/login", params={"username": "nobody-xyz", "password": "any"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_with_token(client, admin_headers):
    r = client.get("/auth/me", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_password_strength_weak(client):
    r = client.post("/auth/check-strength", params={"password": "123"})
    assert r.status_code == 200
    assert r.json()["valid"] is False


def test_password_strength_strong(client):
    r = client.post("/auth/check-strength", params={"password": "StrongP@ssw0rd!"})
    assert r.status_code == 200
    assert r.json()["valid"] is True