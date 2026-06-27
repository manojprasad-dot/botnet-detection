import pytest
from httpx import AsyncClient

from database.models.user import UserRole


@pytest.mark.asyncio
async def test_register_login_flow(client: AsyncClient):
    """Test user registration, login, profile retrieval, and token refresh."""
    # 1. Register a new user
    register_data = {
        "email": "new_viewer@kovirx.com",
        "username": "new_viewer",
        "password": "SecurePassword123!",
        "role": UserRole.viewer.value,
    }
    response = await client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == register_data["email"]
    assert user_data["username"] == register_data["username"]
    assert "id" in user_data

    # 2. Login with correct credentials
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"],
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 3. Retrieve user profile using Bearer JWT
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["email"] == register_data["email"]
    assert profile_data["role"] == UserRole.viewer.value

    # 4. Refresh access token using refresh token
    refresh_data = {
        "refresh_token": token_data["refresh_token"],
    }
    response = await client.post("/api/v1/auth/refresh", json=refresh_data)
    assert response.status_code == 200
    new_token_data = response.json()
    assert "access_token" in new_token_data
    assert "refresh_token" in new_token_data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Verify login fails with wrong credentials."""
    login_data = {
        "email": "nonexistent@kovirx.com",
        "password": "WrongPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient, test_user):
    """Test forgot password mock handler."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_user.email},
    )
    assert response.status_code == 200
    assert "message" in response.json()
