from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for error in exc.errors():
        msg = error.get("msg", "")
        if isinstance(msg, str) and msg.startswith("Value error, "):
            msg = msg[13:]
        error_messages.append(msg)

    detail_message = "; ".join(error_messages)
    return JSONResponse(status_code=422, content={"detail": detail_message})
