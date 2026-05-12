import json

from redis.asyncio import Redis


class RedisMemoryStore:
    def __init__(self, redis_url: str, ttl_seconds: int = 60 * 60 * 24 * 7) -> None:
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    async def get_session(self, user_id: str, session_id: str) -> list[dict[str, str]]:
        raw = await self.redis.get(self._key(user_id, session_id))
        return json.loads(raw) if raw else []

    async def append_turn(self, user_id: str, session_id: str, query: str, answer: str) -> None:
        key = self._key(user_id, session_id)
        history = await self.get_session(user_id, session_id)
        history.extend([{"role": "user", "content": query}, {"role": "assistant", "content": answer}])
        await self.redis.set(key, json.dumps(history[-20:]), ex=self.ttl_seconds)

    @staticmethod
    def _key(user_id: str, session_id: str) -> str:
        return f"chat:{user_id}:{session_id}"

