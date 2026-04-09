"""Unit tests for logging_config module."""

import json
import logging
from unittest.mock import patch, MagicMock

from src.logging_config import _JSONFormatter, setup_logging, _get_trace_id


def test_json_formatter_basic():
    formatter = _JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    output = formatter.format(record)
    data = json.loads(output)
    assert data["level"] == "INFO"
    assert data["logger"] == "test"
    assert data["msg"] == "hello world"
    assert "ts" in data


def test_json_formatter_with_exception():
    formatter = _JSONFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="fail",
        args=(),
        exc_info=exc_info,
    )
    output = formatter.format(record)
    data = json.loads(output)
    assert "exc" in data
    assert "boom" in data["exc"]


def test_json_formatter_with_trace_id():
    formatter = _JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="traced",
        args=(),
        exc_info=None,
    )
    with patch("src.logging_config._get_trace_id", return_value="abc123"):
        output = formatter.format(record)
    data = json.loads(output)
    assert data.get("trace_id") == "abc123"


def test_get_trace_id_no_otel():
    with patch("opentelemetry.trace") as mock_trace:
        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.is_valid = False
        mock_span.get_span_context.return_value = mock_ctx
        mock_trace.get_current_span.return_value = mock_span
        result = _get_trace_id()
    assert result is None


def test_get_trace_id_valid():
    with patch("opentelemetry.trace") as mock_trace:
        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.is_valid = True
        mock_ctx.trace_id = 0x1234567890ABCDEF
        mock_span.get_span_context.return_value = mock_ctx
        mock_trace.get_current_span.return_value = mock_span
        result = _get_trace_id()
    assert result == format(0x1234567890ABCDEF, "032x")


def test_get_trace_id_exception():
    with patch.dict("sys.modules", {"opentelemetry": None, "opentelemetry.trace": None}):
        result = _get_trace_id()
    assert result is None


def test_setup_logging_json_format():
    setup_logging(level="DEBUG", json_format=True)
    handler = logging.root.handlers[0]
    assert isinstance(handler.formatter, _JSONFormatter)
    assert logging.root.level == logging.DEBUG


def test_setup_logging_plain_format():
    setup_logging(level="WARNING", json_format=False)
    handler = logging.root.handlers[0]
    assert not isinstance(handler.formatter, _JSONFormatter)
    assert logging.root.level == logging.WARNING
