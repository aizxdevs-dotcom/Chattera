# app/services/presence_manager.py
from datetime import datetime
from redis.asyncio import Redis
from app import config

PREFIX = "presence:user"
TTL_SECONDS = 300

async def get_redis():
    """Create a Redis client bound to the current loop."""
    return Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        username=config.REDIS_USERNAME,
        password=config.REDIS_PASSWORD,
        ssl=config.REDIS_SSL,
        decode_responses=True,
    )

async def mark_user_active(user_id: str):
    async with await get_redis() as r:
        await r.set(f"{PREFIX}:{user_id}", datetime.utcnow().isoformat(), ex=TTL_SECONDS)

async def mark_user_inactive(user_id: str):
    async with await get_redis() as r:
        await r.delete(f"{PREFIX}:{user_id}")

async def get_active_user_ids() -> list[str]:
    ids: list[str] = []
    async with await get_redis() as r:
        async for key in r.scan_iter(f"{PREFIX}:*"):
            ids.append(key.split(":")[-1])
    return ids

async def is_user_active(user_id: str) -> bool:
    async with await get_redis() as r:
        return await r.exists(f"{PREFIX}:{user_id}") == 1