"""Unit tests for tracing.py."""

from unittest.mock import MagicMock, patch


def test_setup_tracing():
    mock_app = MagicMock()
    mock_engine = MagicMock()
    mock_engine_null_pool = MagicMock()

    with (
        patch("src.config.settings") as mock_settings,
        patch("src.tracing.Resource") as mock_resource,
        patch("src.tracing.TracerProvider") as mock_provider_cls,
        patch("src.tracing.OTLPSpanExporter"),
        patch("src.tracing.BatchSpanProcessor"),
        patch("src.tracing.trace") as mock_trace,
        patch("src.tracing.FastAPIInstrumentor") as mock_fastapi_instr,
        patch("src.tracing.SQLAlchemyInstrumentor") as mock_sqla_instr,
    ):
        mock_settings.OTEL_SERVICE_NAME = "test-service"
        mock_settings.OTEL_SAMPLE_RATE = 1.0
        mock_settings.OTEL_ENDPOINT = "http://localhost:4317"

        from src.tracing import setup_tracing

        setup_tracing(mock_app, mock_engine, mock_engine_null_pool)

        mock_resource.create.assert_called_once()
        mock_provider_cls.assert_called_once()
        mock_trace.set_tracer_provider.assert_called_once()
        mock_fastapi_instr.instrument_app.assert_called_once_with(
            mock_app, excluded_urls="/metrics"
        )
        assert mock_sqla_instr.return_value.instrument.call_count == 2
