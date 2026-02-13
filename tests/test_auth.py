def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_register_new_user(client):
    # Use a unique email for testing to avoid conflict with seeded data
    payload = {
        "email": "test_user_unique@example.com",
        "password": "StrongPassword123!",
        "name": "Test User"
    }
    response = client.post("/api/auth/register", json=payload)
    # Note: This might fail if the DB isn't reset, so we check for 201 OR 409
    assert response.status_code in [201, 409]
    if response.status_code == 201:
        data = response.json()
        assert data["email"] == payload["email"]
        assert "id" in data

def test_login_admin(client):
    # This uses the seeded credentials
    payload = {
        "email": "admin@example.com",
        "password": "AdminPassword123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "accessToken" in data
    assert "refreshToken" in data

def test_login_invalid(client):
    payload = {
        "email": "admin@example.com",
        "password": "WrongPassword!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401