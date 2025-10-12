# src/exception_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Перехватывает ошибки валидации Pydantic v2 и возвращает русские сообщения
    в формате одной строки через '; '.
    """
    error_messages = []

    for error in exc.errors():
        msg = error.get("msg", "")
        err_type = error.get("type", "")
        loc = error.get("loc", ())
        input_value = error.get("input", None)

        # Обработка кастомных ValueError с несколькими ошибками
        if msg.startswith("Value error, ") and ";" in msg:
            custom_errors = msg[13:].split("; ")
            error_messages.extend(custom_errors)
            continue

        # Обработка одиночных кастомных ValueError
        elif msg.startswith("Value error, "):
            error_messages.append(msg[13:])
            continue

        # Пропущенные обязательные поля
        if msg == "Field required":
            field_name = loc[-1] if loc else "неизвестное поле"
            error_messages.append(
                f"Поле '{field_name}' обязательно для заполнения")

        # Неверный тип данных
        elif err_type.startswith("type_error"):
            if "int" in err_type and input_value is None:
                field_name = loc[-1] if loc else "неизвестное поле"
                error_messages.append(
                    f"Поле '{field_name}' обязательно для заполнения")
            else:
                field_name = loc[-1] if loc else "неизвестное поле"
                error_messages.append(
                    f"Поле '{field_name}' имеет неверный тип данных")

        # Другие ошибки
        else:
            error_messages.append(msg)

    # Убираем дубликаты и объединяем
    unique_errors = list(dict.fromkeys(error_messages))
    detail_message = "; ".join(unique_errors)

    return JSONResponse(status_code=422, content={"detail": detail_message})


async def json_decode_exception_handler(request: Request, exc: Exception):
    """
    Перехватывает ошибки декодирования JSON.
    """
    error_message = "Ошибка в формате JSON данных"

    # Более детальный анализ ошибки
    if "expecting value" in str(exc):
        error_message = "Неверный формат JSON данных!"
    elif "Expecting value" in str(exc):
        error_message = "Неверный формат JSON данных!"
    elif "Unterminated string" in str(exc):
        error_message = "Незавершенная строка в JSON данных!"
    elif "Invalid numeric literal" in str(exc):
        error_message = "Неверный числовой формат в JSON данных!"
    elif "Invalid \\u" in str(exc):
        error_message = "Неверная escape-последовательность в JSON данных!"

    return JSONResponse(
        status_code=422,
        content={"detail": error_message}
    )
