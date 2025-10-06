import re
from typing import Any


def validate_email_russian(value: Any) -> str:
    """Валидация email с русскими сообщениями об ошибках"""
    if not isinstance(value, str):
        raise ValueError("Email должен быть строкой")

    value = value.strip()

    if not value:
        raise ValueError("Email не может быть пустым")

    if "@" not in value:
        raise ValueError("Email должен содержать символ @")

    parts = value.split('@', 1)
    local_part, domain = parts

    if not local_part:
        raise ValueError("В email должна быть часть перед символом @")

    if not domain:
        raise ValueError("В email должна быть часть после символа @")

    if "." not in domain:
        raise ValueError("Некорректный домен в email адресе")

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, value):
        raise ValueError("Некорректный формат email адреса")

    return value


def validate_password_russian(value: Any) -> str:
    """Валидация пароля с русскими сообщениями об ошибках"""
    if not isinstance(value, str):
        raise ValueError("Пароль должен быть строкой")

    if not value or not value.strip():
        raise ValueError("Пароль не может быть пустым")

    if len(value) < 8:
        raise ValueError("Пароль должен содержать минимум 8 символов")

    if len(value) > 100:
        raise ValueError("Пароль должен содержать максимум 100 символов")

    if not any(c.isupper() for c in value):
        raise ValueError(
            "Пароль должен содержать хотя бы одну заглавную букву")

    if not any(c.islower() for c in value):
        raise ValueError("Пароль должен содержать хотя бы одну строчную букву")

    if not any(c.isdigit() for c in value):
        raise ValueError("Пароль должен содержать хотя бы одну цифру")

    if any(c.isspace() for c in value):
        raise ValueError("Пароль не должен содержать пробелы")

    return value
