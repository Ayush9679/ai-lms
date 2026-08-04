"""
AI-LMS Auth Tests — registration, login, token refresh, email verification.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """App should return healthy status."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_register_student(client: AsyncClient):
    """Students can register successfully."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "password": "SecurePass123!",
            "role": "student",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "jane@example.com"
    assert data["role"] == "student"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_teacher(client: AsyncClient):
    """Teachers can register successfully."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Prof Smith",
            "email": "prof@example.com",
            "password": "TeachPass123!",
            "role": "teacher",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "teacher"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registering with an existing email returns 409."""
    payload = {
        "full_name": "Duplicate User",
        "email": "dup@example.com",
        "password": "DupPass123!",
        "role": "student",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Weak passwords are rejected."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Weak User",
            "email": "weak@example.com",
            "password": "password",  # No uppercase, no digit
            "role": "student",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_admin_forbidden(client: AsyncClient):
    """Self-registration as admin is forbidden."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Hacker",
            "email": "hacker@example.com",
            "password": "HackPass123!",
            "role": "admin",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Valid credentials return a token pair."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Login User",
            "email": "login@example.com",
            "password": "LoginPass123!",
            "role": "student",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "LoginPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Wrong password returns 401."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Wrong Pass",
            "email": "wrongpass@example.com",
            "password": "RightPass123!",
            "role": "student",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "WrongPass999!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient):
    """Authenticated user can get their own profile."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Me User",
            "email": "me@example.com",
            "password": "MePass123!",
            "role": "student",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "MePass123!"},
    )
    token = login.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    """Unauthenticated request to /me returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """Valid refresh token returns new token pair."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Refresh User",
            "email": "refresh@example.com",
            "password": "RefreshPass123!",
            "role": "student",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "RefreshPass123!"},
    )
    refresh_token = login.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_forgot_password(client: AsyncClient):
    """Forgot password always returns success (no email enumeration)."""
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == 200
    assert "sent" in response.json()["message"].lower()
