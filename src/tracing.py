import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def setup_tracing(app, engine, engine_null_pool) -> None:
    """Инициализирует OpenTelemetry tracing с OTLP экспортом в Tempo."""
    from src.config import settings

    resource = Resource.create({"service.name": settings.OTEL_SERVICE_NAME})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(endpoint=settings.OTEL_ENDPOINT, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    # AsyncEngine требует .sync_engine для инструментации
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine, enable_commenter=True)
    SQLAlchemyInstrumentor().instrument(engine=engine_null_pool.sync_engine, enable_commenter=True)

    logger.info("OpenTelemetry tracing initialized", extra={"endpoint": settings.OTEL_ENDPOINT})
