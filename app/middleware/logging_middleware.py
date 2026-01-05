import time
from typing import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        log = logger.bind(context="http")
        request_id = str(uuid4())
        request.state.request_id = request_id

        start_time = time.time()

        log.info(
            (
                "Request started with id: {request_id}, method: {method},"
                "url: {url}, client_ip: {client_ip}, user_agent: {user_agent}"
            ),
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
        )

        try:
            response = await call_next(request)

            process_time = (time.time() - start_time) * 1000

            log.info(
                (
                    "Request completed with id: {request_id}, method: {method},"
                    "url: {url}, status_code: {status_code}, "
                    "working time: {process_time}, response size: {response_size}"
                ),
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=f"{process_time:.2f}ms",
                response_size=response.headers.get("content-length", 0),
            )
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            process_time = (time.time() - start_time) * 1000

            log.exception(
                (
                    "Request completed with id: {request_id}, method: {method},"
                    "url: {url}, working time: {process_time}, error: {error}"
                ),
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                process_time=f"{process_time:.2f}ms",
                error=exc,
                exc_info=True,
            )
            raise
