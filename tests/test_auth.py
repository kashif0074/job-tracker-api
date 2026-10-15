def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


def test_register_and_login(client):
    r = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert r.status_code == 201
    assert r.json()["email"] == "alice@example.com"

    r = client.post(
        "/auth/login",
        data={"username": "alice@example.com", "password": "password123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_duplicate_email_rejected(client):
    client.post("/auth/register", json={"email": "d@example.com", "password": "password123"})
    r = client.post("/auth/register", json={"email": "d@example.com", "password": "password123"})
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"].lower()


def test_wrong_password_rejected(client):
    client.post("/auth/register", json={"email": "w@example.com", "password": "password123"})
    r = client.post("/auth/login", data={"username": "w@example.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_protected_endpoint_requires_auth(client):
    r = client.get("/jobs")
    assert r.status_code == 401


def test_me_endpoint(client, auth_headers):
    r = client.get("/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "user@example.com"


def test_invalid_token_rejected(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401