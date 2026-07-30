"""Request-ID context propagation for structured logging."""

from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    return request_id_var.get()


class LogContextMiddleware(BaseHTTPMiddleware):
    """Extract Kong-Request-ID from incoming requests and set it in context."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("Kong-Request-ID", str(uuid4()))
        token = request_id_var.set(request_id)
        try:
            return await call_next(request)
        finally:
            request_id_var.reset(token)
