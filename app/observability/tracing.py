from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

from app.core.config import Settings


def configure_tracing(settings: Settings) -> None:
    resource = Resource.create({"service.name": settings.app_name, "deployment.environment": settings.environment})
    trace.set_tracer_provider(TracerProvider(resource=resource))

