"""Unit tests for exception_handlers."""

import json
from unittest.mock import AsyncMock

from fastapi.exceptions import RequestValidationError

from src.exception_handlers import (
    json_decode_exception_handler,
    validation_exception_handler,
)


def _make_request():
    return AsyncMock()


async def test_validation_field_required():
    exc = RequestValidationError(
        errors=[
            {"msg": "Field required", "type": "missing", "loc": ("body", "name"), "input": None}
        ]
    )
    resp = await validation_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert resp.status_code == 422
    assert "Поле 'name' обязательно" in data["detail"]


async def test_validation_custom_value_error_single():
    exc = RequestValidationError(
        errors=[
            {
                "msg": "Value error, Имя слишком короткое",
                "type": "value_error",
                "loc": ("body",),
                "input": None,
            }
        ]
    )
    resp = await validation_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert "Имя слишком короткое" in data["detail"]


async def test_validation_custom_value_error_multiple():
    exc = RequestValidationError(
        errors=[
            {
                "msg": "Value error, Ошибка 1; Ошибка 2",
                "type": "value_error",
                "loc": ("body",),
                "input": None,
            }
        ]
    )
    resp = await validation_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert "Ошибка 1" in data["detail"]
    assert "Ошибка 2" in data["detail"]


async def test_validation_type_error():
    exc = RequestValidationError(
        errors=[
            {
                "msg": "Input should be valid",
                "type": "type_error.integer",
                "loc": ("body", "price"),
                "input": "abc",
            }
        ]
    )
    resp = await validation_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert "неверный тип данных" in data["detail"]


async def test_validation_type_error_int_none():
    exc = RequestValidationError(
        errors=[
            {
                "msg": "Input should be valid",
                "type": "type_error.int",
                "loc": ("body", "count"),
                "input": None,
            }
        ]
    )
    resp = await validation_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert "обязательно" in data["detail"]


async def test_validation_deduplication():
    exc = RequestValidationError(
        errors=[
            {"msg": "Field required", "type": "missing", "loc": ("body", "x"), "input": None},
            {"msg": "Field required", "type": "missing", "loc": ("body", "x"), "input": None},
        ]
    )
    resp = await validation_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    # Duplicates removed
    assert data["detail"].count("Поле 'x'") == 1


async def test_validation_other_error():
    exc = RequestValidationError(
        errors=[
            {
                "msg": "String too short",
                "type": "string_too_short",
                "loc": ("body", "name"),
                "input": "a",
            }
        ]
    )
    resp = await validation_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert "String too short" in data["detail"]


async def test_json_decode_expecting_value():
    exc = json.JSONDecodeError("Expecting value", "", 0)
    resp = await json_decode_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert resp.status_code == 422
    assert "Неверный формат JSON" in data["detail"]


async def test_json_decode_unterminated():
    exc = Exception("Unterminated string starting at")
    resp = await json_decode_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert "Незавершенная строка" in data["detail"]


async def test_json_decode_invalid_numeric():
    exc = Exception("Invalid numeric literal")
    resp = await json_decode_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert "числовой формат" in data["detail"]


async def test_json_decode_invalid_escape():
    exc = Exception("Invalid \\u escape")
    resp = await json_decode_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert "escape" in data["detail"]


async def test_json_decode_generic():
    exc = Exception("some unknown error")
    resp = await json_decode_exception_handler(_make_request(), exc)
    data = json.loads(resp.body)
    assert data["detail"] == "Ошибка в формате JSON данных"
