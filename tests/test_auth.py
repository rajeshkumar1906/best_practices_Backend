import pytest
from httpx import AsyncClient


class TestSignup:
    @pytest.mark.asyncio
    async def test_successful_signup(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"name": "Rajesh", "email": "rajesh@example.com", "password": "Password123!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Rajesh"
        assert data["email"] == "rajesh@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_duplicate_email(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"name": "Another", "email": test_user.email, "password": "Password123!"},
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "User already exists"

    @pytest.mark.asyncio
    async def test_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"name": "Test", "email": "invalid-email", "password": "Password123!"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_weak_password(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"name": "Test", "email": "test@example.com", "password": "weak"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_password_hashed_not_stored_plain(self, client: AsyncClient, test_session):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"name": "Test", "email": "newuser@example.com", "password": "Password123!"},
        )
        assert response.status_code == 201

        from sqlalchemy import select
        from app.db.models import User

        result = await test_session.execute(select(User).where(User.email == "newuser@example.com"))
        user = result.scalar_one()
        assert user.password_hash != "Password123!"
        assert len(user.password_hash) > 50


class TestSignin:
    @pytest.mark.asyncio
    async def test_successful_signin(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/signin",
            json={"email": test_user.email, "password": "Password123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    @pytest.mark.asyncio
    async def test_wrong_password(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/signin",
            json={"email": test_user.email, "password": "WrongPassword123!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_unknown_email(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/auth/signin",
            json={"email": "unknown@example.com", "password": "Password123!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    @pytest.mark.asyncio
    async def test_jwt_contains_expected_claims(self, client: AsyncClient, test_user):
        from jose import jwt
        from app.core.config import get_settings

        settings = get_settings()
        response = await client.post(
            "/api/v1/auth/signin",
            json={"email": test_user.email, "password": "Password123!"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == str(test_user.id)
        assert "exp" in payload

    @pytest.mark.asyncio
    async def test_expired_token(self, client: AsyncClient, expired_token):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, client: AsyncClient, auth_token, test_user):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.asyncio
    async def test_missing_token(self, client: AsyncClient):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401
        assert "Missing authorization header" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_token(self, client: AsyncClient):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_expired_token(self, client: AsyncClient, expired_token):
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_user_not_found(self, client: AsyncClient):
        from app.core.security import create_access_token
        fake_token = create_access_token(subject="999999")
        response = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 401
        assert "User not found" in response.json()["detail"]


class TestDatabase:
    @pytest.mark.asyncio
    async def test_user_persistence(self, client: AsyncClient, test_session):
        from sqlalchemy import select
        from app.db.models import User

        response = await client.post(
            "/api/v1/auth/signup",
            json={"name": "Persist", "email": "persist@example.com", "password": "Password123!"},
        )
        assert response.status_code == 201

        result = await test_session.execute(select(User).where(User.email == "persist@example.com"))
        user = result.scalar_one()
        assert user is not None
        assert user.name == "Persist"
        assert user.email == "persist@example.com"

    @pytest.mark.asyncio
    async def test_unique_email_constraint(self, client: AsyncClient, test_user):
        response = await client.post(
            "/api/v1/auth/signup",
            json={"name": "Another", "email": test_user.email, "password": "Password123!"},
        )
        assert response.status_code == 409