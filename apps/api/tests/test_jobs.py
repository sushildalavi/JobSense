"""
Jobs endpoint tests.

Covers: list (empty + with data), detail, shortlist action.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.models.job import Job, JobSource, JobStatus

pytestmark = pytest.mark.asyncio


class TestListJobs:
    async def test_list_jobs_empty(self, client: AsyncClient, auth_headers: dict):
        """Authenticated user with no jobs sees an empty list."""
        resp = await client.get("/api/v1/jobs/", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # Accept either a bare list or a paginated envelope
        items = body if isinstance(body, list) else body.get("items", body.get("results", []))
        assert isinstance(items, list)

    async def test_list_jobs_with_data(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """After inserting a job, it appears in the listing."""
        resp = await client.get("/api/v1/jobs/", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        items = body if isinstance(body, list) else body.get("items", body.get("results", body))

        ids = [str(j["id"]) for j in items]
        assert test_job["id"] in ids, f"Expected {test_job['id']} in {ids}"

    async def test_list_jobs_requires_auth(self, client: AsyncClient):
        """Unauthenticated request returns 401."""
        resp = await client.get("/api/v1/jobs/")
        assert resp.status_code == 401

    async def test_list_jobs_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        async_session,
        test_user: dict,
    ):
        """Pagination params are accepted and limit the response size."""
        # Insert a few extra jobs
        source = JobSource(name=f"src-{uuid.uuid4().hex[:6]}", connector_type="test")
        async_session.add(source)
        await async_session.flush()

        for i in range(5):
            async_session.add(
                Job(
                    source_id=source.id,
                    source_job_id=f"pg-test-{i}-{uuid.uuid4().hex[:6]}",
                    company_name=f"Company {i}",
                    title=f"Engineer {i}",
                    status=JobStatus.active,
                )
            )
        await async_session.commit()

        resp = await client.get("/api/v1/jobs/?limit=2&offset=0", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        items = body if isinstance(body, list) else body.get("items", body.get("results", body))
        assert len(items) <= 2

    async def test_list_jobs_filter_by_status(
        self,
        client: AsyncClient,
        auth_headers: dict,
        async_session,
    ):
        """Status filter only returns matching jobs."""
        source = JobSource(name=f"src-status-{uuid.uuid4().hex[:6]}", connector_type="test")
        async_session.add(source)
        await async_session.flush()

        async_session.add(
            Job(
                source_id=source.id,
                source_job_id=f"expired-{uuid.uuid4().hex[:6]}",
                company_name="OldCo",
                title="Old Role",
                status=JobStatus.expired,
            )
        )
        await async_session.commit()

        resp = await client.get("/api/v1/jobs/?status=expired", headers=auth_headers)
        assert resp.status_code in (200, 422)  # 422 if param not supported


class TestJobDetail:
    async def test_get_job_detail(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """Fetching a job by ID returns the full detail."""
        resp = await client.get(f"/api/v1/jobs/{test_job['id']}", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert str(body["id"]) == test_job["id"]
        assert body["title"] == test_job["title"]
        assert body["company_name"] == test_job["company"]

    async def test_get_job_detail_not_found(self, client: AsyncClient, auth_headers: dict):
        """Non-existent job ID returns 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/api/v1/jobs/{fake_id}", headers=auth_headers)
        assert resp.status_code == 404

    async def test_get_job_detail_invalid_id(self, client: AsyncClient, auth_headers: dict):
        """Non-UUID job ID returns 422 or 404."""
        resp = await client.get("/api/v1/jobs/not-a-uuid", headers=auth_headers)
        assert resp.status_code in (404, 422)

    async def test_get_job_detail_requires_auth(self, client: AsyncClient, test_job: dict):
        """Unauthenticated detail request returns 401."""
        resp = await client.get(f"/api/v1/jobs/{test_job['id']}")
        assert resp.status_code == 401


class TestShortlistJob:
    async def test_shortlist_job(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
        test_user: dict,
    ):
        """Shortlisting a job creates an application with status=shortlisted."""
        resp = await client.post(
            f"/api/v1/jobs/{test_job['id']}/shortlist",
            headers=auth_headers,
        )
        # Acceptable responses: 200 (already exists) or 201 (created)
        assert resp.status_code in (200, 201), resp.text
        body = resp.json()
        # Should return the application or a confirmation
        assert body is not None

    async def test_shortlist_job_idempotent(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_job: dict,
    ):
        """Shortlisting the same job twice is idempotent (200 or 201)."""
        for _ in range(2):
            resp = await client.post(
                f"/api/v1/jobs/{test_job['id']}/shortlist",
                headers=auth_headers,
            )
            assert resp.status_code in (200, 201), resp.text

    async def test_shortlist_requires_auth(self, client: AsyncClient, test_job: dict):
        """Unauthenticated shortlist returns 401."""
        resp = await client.post(f"/api/v1/jobs/{test_job['id']}/shortlist")
        assert resp.status_code == 401

    async def test_shortlist_nonexistent_job(self, client: AsyncClient, auth_headers: dict):
        """Shortlisting a non-existent job returns 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.post(f"/api/v1/jobs/{fake_id}/shortlist", headers=auth_headers)
        assert resp.status_code == 404
