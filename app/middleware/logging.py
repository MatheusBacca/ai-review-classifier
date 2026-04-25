"""HTTP middleware for structured request/response logging."""

from __future__ import annotations

import json
import logging
import time
from typing import Any
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.logging import reset_request_id, set_request_id

LOGGER = logging.getLogger("app.http")
IDEMPOTENCY_HEADERS = ("idempotency-key", "x-idempotency-key", "x-request-id")
SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie"}
BODY_LOG_LIMIT = 4000


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log incoming requests and outgoing responses with request id tracking.

    Example:
        >>> # app.add_middleware(RequestLoggingMiddleware)
        >>> True
        True
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response details for observability.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/route callable.

        Returns:
            HTTP response returned by downstream stack.

        Raises:
            Exception: Re-raises any downstream exception after logging.
        """
        request_id = self._resolve_request_id(request)
        token = set_request_id(request_id)
        start_time = time.perf_counter()

        request_payload = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "path_params": dict(request.path_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_ip": request.client.host if request.client else None,
            "request_id": request_id,
            "body": await self._extract_request_body(request),
        }
        LOGGER.info("Incoming HTTP request.", extra={"event": "http_request_in", "http": request_payload})

        try:
            response = await call_next(request)
        except Exception as error:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            LOGGER.exception(
                "HTTP request failed.",
                extra={
                    "event": "http_request_error",
                    "http": {
                        "method": request.method,
                        "path": request.url.path,
                        "request_id": request_id,
                        "duration_ms": duration_ms,
                        "error_type": type(error).__name__,
                    },
                },
            )
            reset_request_id(token)
            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-Id"] = request_id
        response_payload = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "request_id": request_id,
            "duration_ms": duration_ms,
            "response_headers": self._sanitize_headers(dict(response.headers)),
        }
        LOGGER.info("Outgoing HTTP response.", extra={"event": "http_request_out", "http": response_payload})
        reset_request_id(token)
        return response

    @staticmethod
    def _resolve_request_id(request: Request) -> str:
        """Resolve request id from idempotency-related headers.

        Args:
            request: Incoming HTTP request.

        Returns:
            Request id from known headers or generated UUID.
        """
        for header_name in IDEMPOTENCY_HEADERS:
            header_value = request.headers.get(header_name)
            if header_value:
                return header_value
        return str(uuid4())

    @staticmethod
    def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
        """Hide sensitive header values before logging.

        Args:
            headers: Raw headers dictionary.

        Returns:
            Sanitized headers dictionary.
        """
        sanitized_headers: dict[str, str] = {}
        for key, value in headers.items():
            if key.lower() in SENSITIVE_HEADERS:
                sanitized_headers[key] = "***"
            else:
                sanitized_headers[key] = value
        return sanitized_headers

    async def _extract_request_body(self, request: Request) -> Any:
        """Extract request body content in a logging-safe format.

        Args:
            request: Incoming HTTP request.

        Returns:
            Parsed JSON, text snippet, or ``None`` when body is absent.
        """
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return None

        body_bytes = await request.body()
        request._body = body_bytes  # keep body available for downstream consumers
        if not body_bytes:
            return None

        if len(body_bytes) > BODY_LOG_LIMIT:
            return {"truncated": True, "size_bytes": len(body_bytes)}

        body_text = body_bytes.decode("utf-8", errors="replace")
        try:
            return json.loads(body_text)
        except json.JSONDecodeError:
            return body_text
