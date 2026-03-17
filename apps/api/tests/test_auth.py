"""
Auth endpoint tests.

Covers: register, login, wrong-password, /me, token refresh.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        """New user can register and receives tokens."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@applyflow.dev",
                "password": "SecurePass9",
                "full_name": "New User",
            },
        )
        assert resp.status_code in (200, 201), resp.text
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: dict):
        """Registering with an existing email returns 400 or 409."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user["email"],
                "password": "SecurePass9",
                "full_name": "Duplicate",
            },
        )
        assert resp.status_code in (400, 409), resp.text

    async def test_register_weak_password(self, client: AsyncClient):
        """Password without digits is rejected by schema validation (422)."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@applyflow.dev",
                "password": "NoDigitsHere",
                "full_name": "Weak Pass",
            },
        )
        assert resp.status_code == 422

    async def test_register_missing_fields(self, client: AsyncClient):
        """Missing required fields returns 422."""
        resp = await client.post("/api/v1/auth/register", json={"email": "x@y.com"})
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Valid credentials return access token."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0

    async def test_login_wrong_password(self, client: AsyncClient, test_user: dict):
        """Wrong password returns 401."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user["email"], "password": "WrongPass99"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient):
        """Unknown email returns 401 (not 404, to prevent user enumeration)."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@applyflow.dev", "password": "SomePass1"},
        )
        assert resp.status_code == 401

    async def test_login_invalid_email_format(self, client: AsyncClient):
        """Malformed email is rejected at schema level (422)."""
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "SomePass1"},
        )
        assert resp.status_code == 422


class TestGetMe:
    async def test_get_me_authenticated(self, client: AsyncClient, test_user: dict, auth_headers: dict):
        """Authenticated user can fetch their own profile."""
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["email"] == test_user["email"]
        assert body["full_name"] == test_user["full_name"]
        # Sensitive fields must not be leaked
        assert "hashed_password" not in body
        assert "google_tokens" not in body

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Request without token returns 401."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Malformed token returns 401."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        assert resp.status_code == 401


class TestRefreshToken:
    async def test_refresh_token_success(self, client: AsyncClient, test_user: dict):
        """Valid refresh token returns a new access token."""
        # First login to get a refresh token.
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": test_user["email"], "password": test_user["password"]},
        )
        assert login_resp.status_code == 200
        refresh_token = login_resp.json().get("refresh_token")

        if refresh_token is None:
            pytest.skip("Endpoint does not return a refresh token — skipping")

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200, resp.text
        assert "access_token" in resp.json()

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Expired or invalid refresh token returns 401."""
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "completely.invalid.token"},
        )
        assert resp.status_code in (401, 422)
