from typing import Any, Protocol, ContextManager


class TraceClient(Protocol):
    def safe_start_trace(self, trace_id: str, name: str, payload: dict[str, Any]) -> ContextManager[Any]:
        ...

