from typing import Any, Protocol


class TraceClient(Protocol):
    def start_trace(self, trace_id: str, name: str, payload: dict[str, Any]) -> None:
        ...

    def end_trace(self, trace_id: str, payload: dict[str, Any]) -> None:
        ...

