"""
Redis client setup and dependency injection.
"""
from __future__ import annotations

from typing import AsyncGenerator, Optional

import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


async def create_redis_pool() -> aioredis.Redis:
    """
    Create and return an async Redis connection pool.

    Called once during application startup and stored on app.state.
    """
    pool = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    await pool.ping()
    logger.info("Redis ping succeeded", url=settings.REDIS_URL)
    return pool


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI dependency that yields the shared Redis client.

    Usage::

        @router.get("/example")
        async def example(redis: aioredis.Redis = Depends(get_redis)):
            ...
    """
    from main import app  # local import to avoid circular dependency

    yield app.state.redis


class RedisClient:
    """
    Thin wrapper around an async Redis client with convenience helpers.

    Accepts an existing aioredis.Redis instance so it can be used both
    inside FastAPI (via Depends) and inside Celery tasks.
    """

    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    # ── Basic CRUD ────────────────────────────────────────────────────────────

    async def get(self, key: str) -> Optional[str]:
        """Get a string value by key, returns None if missing."""
        return await self._client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        expire_seconds: Optional[int] = None,
    ) -> bool:
        """Set a string value, optionally with a TTL in seconds."""
        if expire_seconds:
            return bool(await self._client.setex(key, expire_seconds, value))
        return bool(await self._client.set(key, value))

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys. Returns count of deleted keys."""
        return await self._client.delete(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set or update TTL on an existing key."""
        return bool(await self._client.expire(key, seconds))

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        return bool(await self._client.exists(key))

    async def incr(self, key: str, amount: int = 1) -> int:
        """Atomically increment an integer counter."""
        return await self._client.incrby(key, amount)

    async def lpush(self, key: str, *values: str) -> int:
        """Push values to the head of a list."""
        return await self._client.lpush(key, *values)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list[str]:
        """Retrieve a range of values from a list."""
        return await self._client.lrange(key, start, end)

    async def publish(self, channel: str, message: str) -> int:
        """Publish a message to a pub/sub channel."""
        return await self._client.publish(channel, message)

    # ── Rate-limit helper ─────────────────────────────────────────────────────

    async def rate_limit_check(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """
        Sliding-window rate-limit check using Redis INCR + EXPIRE.

        Returns:
            (allowed: bool, current_count: int)
        """
        key = f"rl:{identifier}"
        current = await self.incr(key)
        if current == 1:
            await self.expire(key, window_seconds)
        allowed = current <= max_requests
        return allowed, current
