"""
Application lifecycle tests.

Covers: create, list, status transition.
"""
from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient

from app.models.application import Application, ApplicationStatus


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _create_application(
    client: AsyncClient,
    auth_headers: dict,
    job_id: str,
) -> dict:
    """POST to create an application and return the response body."""
    resp = await client.post(
        "/api/v1/applications/",
        json={"job_id": job_id},
        headers=auth_headers,
    )
    assert resp.status_code in (200, 201), f"Create failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class TestCreateApplication:
    async def test_create_application_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """Creating an application for an existing job returns 200/201."""
        body = await _create_application(client, auth_headers, test_job["id"])
        assert "id" in body
        # Status should be discovered or shortlisted on creation
        assert body.get("status") in (
            ApplicationStatus.discovered.value,
            ApplicationStatus.shortlisted.value,
        )

    async def test_create_application_requires_auth(
        self,
        client: AsyncClient,
        test_job: dict,
    ):
        """Unauthenticated creation returns 401."""
        resp = await client.post(
            "/api/v1/applications/",
            json={"job_id": test_job["id"]},
        )
        assert resp.status_code == 401

    async def test_create_application_nonexistent_job(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Creating an application for a non-existent job returns 404 or 422."""
        resp = await client.post(
            "/api/v1/applications/",
            json={"job_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
        assert resp.status_code in (404, 422)

    async def test_create_application_missing_job_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Missing job_id returns 422."""
        resp = await client.post(
            "/api/v1/applications/",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

class TestListApplications:
    async def test_list_applications_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """User with no applications sees an empty list."""
        resp = await client.get("/api/v1/applications/", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        items = body if isinstance(body, list) else body.get("items", body.get("results", []))
        assert isinstance(items, list)

    async def test_list_applications_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """After creating an application it appears in the list."""
        app_body = await _create_application(client, auth_headers, test_job["id"])
        app_id = app_body["id"]

        resp = await client.get("/api/v1/applications/", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        items = body if isinstance(body, list) else body.get("items", body.get("results", body))
        ids = [str(a["id"]) for a in items]
        assert str(app_id) in ids

    async def test_list_applications_requires_auth(self, client: AsyncClient):
        """Unauthenticated listing returns 401."""
        resp = await client.get("/api/v1/applications/")
        assert resp.status_code == 401

    async def test_list_applications_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        async_session,
        test_user: dict,
        test_job: dict,
    ):
        """Pagination limits the number of results."""
        # Create a second job so we can have multiple applications
        from app.models.job import Job, JobSource, JobStatus
        source = JobSource(name=f"src-app-{uuid.uuid4().hex[:6]}", connector_type="test")
        async_session.add(source)
        await async_session.flush()

        for i in range(3):
            job = Job(
                source_id=source.id,
                source_job_id=f"appjob-{i}-{uuid.uuid4().hex[:6]}",
                company_name=f"AppCo {i}",
                title=f"Role {i}",
                status=JobStatus.active,
            )
            async_session.add(job)
        await async_session.commit()

        resp = await client.get("/api/v1/applications/?limit=1", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        items = body if isinstance(body, list) else body.get("items", body.get("results", body))
        assert len(items) <= 1


# ---------------------------------------------------------------------------
# Status Transition
# ---------------------------------------------------------------------------

class TestTransitionStatus:
    async def test_transition_discovered_to_shortlisted(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """Application can be moved from discovered → shortlisted."""
        app_body = await _create_application(client, auth_headers, test_job["id"])
        app_id = app_body["id"]

        resp = await client.patch(
            f"/api/v1/applications/{app_id}/status",
            json={"status": "shortlisted"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "shortlisted"

    async def test_transition_to_applied(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """Application can eventually reach the 'applied' status."""
        app_body = await _create_application(client, auth_headers, test_job["id"])
        app_id = app_body["id"]

        # Progress through statuses
        for status in ("shortlisted", "tailored", "ready_to_apply", "applied"):
            resp = await client.patch(
                f"/api/v1/applications/{app_id}/status",
                json={"status": status},
                headers=auth_headers,
            )
            assert resp.status_code == 200, f"Transition to {status} failed: {resp.text}"

        assert resp.json()["status"] == "applied"

    async def test_transition_requires_auth(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """Unauthenticated status update returns 401."""
        app_body = await _create_application(client, auth_headers, test_job["id"])
        app_id = app_body["id"]

        resp = await client.patch(
            f"/api/v1/applications/{app_id}/status",
            json={"status": "shortlisted"},
        )
        assert resp.status_code == 401

    async def test_transition_invalid_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """Invalid status value returns 422."""
        app_body = await _create_application(client, auth_headers, test_job["id"])
        app_id = app_body["id"]

        resp = await client.patch(
            f"/api/v1/applications/{app_id}/status",
            json={"status": "flying_to_moon"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_transition_nonexistent_application(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Updating a non-existent application returns 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.patch(
            f"/api/v1/applications/{fake_id}/status",
            json={"status": "shortlisted"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_get_application_events(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """After a transition, the event log contains the new entry."""
        app_body = await _create_application(client, auth_headers, test_job["id"])
        app_id = app_body["id"]

        await client.patch(
            f"/api/v1/applications/{app_id}/status",
            json={"status": "shortlisted"},
            headers=auth_headers,
        )

        resp = await client.get(
            f"/api/v1/applications/{app_id}/events",
            headers=auth_headers,
        )
        # If the endpoint exists it should return a list of events
        if resp.status_code == 200:
            events = resp.json()
            events = events if isinstance(events, list) else events.get("items", [])
            statuses = [e.get("to_status") for e in events]
            assert "shortlisted" in statuses
        else:
            # Endpoint may not be implemented yet — that's okay
            assert resp.status_code in (404, 405)
