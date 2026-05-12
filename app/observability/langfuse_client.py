import contextlib
from typing import Any, ContextManager

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

    def safe_start_trace(self, trace_id: str, name: str, payload: dict[str, Any]) -> ContextManager[Any]:
        logger.info("trace_start", trace_id=trace_id, name=name, payload=payload)
        if self.client:
            try:
                return self.client.start_as_current_observation(
                    name=name,
                    input=payload,
                    trace_context={"trace_id": trace_id},
                    as_type="span",
                )
            except Exception:
                logger.exception("Langfuse tracing failed")
        return contextlib.nullcontext()

