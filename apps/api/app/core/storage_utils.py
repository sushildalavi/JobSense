"""
Async storage helpers — thin wrappers around the sync StorageClient.
"""

from __future__ import annotations

import asyncio

import structlog

logger = structlog.get_logger(__name__)


async def upload_file(
    file_bytes: bytes,
    key: str,
    content_type: str = "application/octet-stream",
    public: bool = False,
) -> str:
    """
    Async wrapper around StorageClient.upload_file.
    Runs the blocking boto3 call in the default executor.
    """
    from app.core.storage import storage

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: storage.upload_file(file_bytes, key, content_type, public),
    )


async def get_file(key: str) -> bytes:
    """Async wrapper around StorageClient.get_file."""
    from app.core.storage import storage

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: storage.get_file(key))


async def delete_file(key: str) -> None:
    """Async wrapper around StorageClient.delete_file."""
    from app.core.storage import storage

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: storage.delete_file(key))


async def generate_presigned_url(
    key: str,
    expires: int = 3600,
    http_method: str = "GET",
) -> str:
    """Async wrapper around StorageClient.generate_presigned_url."""
    from app.core.storage import storage

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: storage.generate_presigned_url(key, expires, http_method),
    )
