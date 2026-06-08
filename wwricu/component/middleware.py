import time
from contextvars import ContextVar
from typing import override

from fastapi import HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware import Middleware
from loguru import logger as log
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class ExceptionMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            raise
        except Exception as e:
            if __debug__:
                raise
            log.exception(f'{request.method} {request.url.path} {e}')
            return JSONResponse(None, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerformanceMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        b = time.time()
        real_ip.set((request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or ''))
        response = await call_next(request)
        log.trace(f'{real_ip.get()} | {request.method} {request.url.path} {response.status_code} {int((time.time() - b) * 1000)} ms')
        return response


real_ip:ContextVar[str] = ContextVar('real_ip', default='')
middlewares = [Middleware(PerformanceMiddleware), Middleware(ExceptionMiddleware)]
