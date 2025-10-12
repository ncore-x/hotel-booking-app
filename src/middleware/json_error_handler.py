import json
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class JSONErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_type = request.headers.get("content-type", "").lower()

        if not content_type.startswith("application/json"):
            return await call_next(request)

        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if body:
                    json.loads(body)

            return await call_next(request)

        except json.JSONDecodeError as exc:
            error_message = "Неверный формат JSON данных!"

            error_str = str(exc)
            if "expecting value" in error_str or "Expecting value" in error_str:
                error_message = "Неверный формат JSON данных: отсутствует значение!"
            elif "Unterminated string" in error_str:
                error_message = "Незавершенная строка в JSON данных!"
            elif "Invalid numeric literal" in error_str:
                error_message = "Неверный числовой формат в JSON данных!"
            elif "Invalid \\u" in error_str:
                error_message = "Неверная escape-последовательность в JSON данных!"
            elif "Extra data" in error_str:
                error_message = "Лишние данные в JSON!"

            return JSONResponse(
                status_code=422,
                content={"detail": error_message}
            )
        except UnicodeDecodeError:
            return await call_next(request)
