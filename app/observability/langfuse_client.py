from typing import Any

import structlog

from app.core.config import Settings

logger = structlog.get_logger(__name__)


class LangfuseTracer:
    def __init__(self, settings: Settings) -> None:
        self.client = None
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                from langfuse import Langfuse

                self.client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
            except Exception as exc:
                logger.warning("langfuse_unavailable", error=str(exc))

    def start_trace(self, trace_id: str, name: str, payload: dict[str, Any]) -> None:
        logger.info("trace_start", trace_id=trace_id, name=name, payload=payload)
        if self.client:
            self.client.trace(id=trace_id, name=name, input=payload)

    def end_trace(self, trace_id: str, payload: dict[str, Any]) -> None:
        logger.info("trace_end", trace_id=trace_id, payload=payload)
        if self.client:
            self.client.trace(id=trace_id, output=payload)

