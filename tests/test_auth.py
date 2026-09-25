def test_signup_success(client):
    response = client.post("/v1/auth/signup", json={
        "email": "newuser@example.com",
        "password": "securepassword",
        "full_name": "New User"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["user"]["email"] == "newuser@example.com"
    assert "access_token" in data["data"]


def test_signup_duplicate_email(client, test_user):
    response = client.post("/v1/auth/signup", json={
        "email": "test@example.com",  # Already exists from fixture
        "password": "password123",
        "full_name": "Another Name"
    })
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_login_success(client, test_user):
    response = client.post("/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_login_wrong_password(client, test_user):
    response = client.post("/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_get_me_success(client, auth_headers):
    response = client.get("/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "test@example.com"


def test_get_me_unauthorized(client):
    # No auth headers provided
    response = client.get("/v1/auth/me")
    assert response.status_code == 401
