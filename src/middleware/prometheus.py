import time

from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Match

REQUESTS = Counter(
    "fastapi_requests_total",
    "Total count of requests by method and path.",
    ["app_name", "method", "path"],
)
RESPONSES = Counter(
    "fastapi_responses_total",
    "Total count of responses by method, path and status code.",
    ["app_name", "method", "path", "status_code"],
)
REQUESTS_DURATION = Histogram(
    "fastapi_requests_duration_seconds",
    "Histogram of request duration by method and path (in seconds).",
    ["app_name", "method", "path"],
)
EXCEPTIONS = Counter(
    "fastapi_exceptions_total",
    "Total count of exceptions by method, path and exception type.",
    ["app_name", "method", "path", "exception_type"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "fastapi_requests_in_progress",
    "Gauge of requests currently being processed by method and path.",
    ["app_name", "method", "path"],
)


BOOKINGS_CREATED = Counter(
    "hotel_booking_bookings_created_total",
    "Total number of bookings successfully created.",
    ["app_name"],
)
BOOKINGS_CANCELLED = Counter(
    "hotel_booking_bookings_cancelled_total",
    "Total number of bookings cancelled.",
    ["app_name"],
)

EXCLUDED_PATHS = {"/metrics"}


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, app_name: str = "fastapi") -> None:
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        method = request.method
        path = self._get_path(request)

        if path in EXCLUDED_PATHS:
            return await call_next(request)

        REQUESTS_IN_PROGRESS.labels(app_name=self.app_name, method=method, path=path).inc()
        REQUESTS.labels(app_name=self.app_name, method=method, path=path).inc()
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            EXCEPTIONS.labels(
                app_name=self.app_name,
                method=method,
                path=path,
                exception_type=type(exc).__name__,
            ).inc()
            raise
        finally:
            duration = time.perf_counter() - start
            RESPONSES.labels(
                app_name=self.app_name, method=method, path=path, status_code=status_code
            ).inc()
            REQUESTS_DURATION.labels(app_name=self.app_name, method=method, path=path).observe(
                duration
            )
            REQUESTS_IN_PROGRESS.labels(app_name=self.app_name, method=method, path=path).dec()

    @staticmethod
    def _get_path(request: Request) -> str:
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return route.path
        return request.url.path
