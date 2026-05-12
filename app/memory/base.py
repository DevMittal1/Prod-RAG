from typing import Protocol


class MemoryStore(Protocol):
    async def get_session(self, user_id: str, session_id: str) -> list[dict[str, str]]:
        ...

    async def append_turn(self, user_id: str, session_id: str, query: str, answer: str) -> None:
        ...

