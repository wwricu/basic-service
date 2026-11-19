import time
from typing import override

from fastapi import HTTPException, Request, Response, status
from fastapi.middleware import Middleware
from fastapi.responses import JSONResponse
from loguru import logger as log
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from wwricu.config import env


class ExceptionMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            raise
        except Exception as e:
            if env.is_dev:
                raise
            log.exception(f'{request.method} {request.url.path} {e}')
            return JSONResponse(None, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerformanceMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        b = time.time()
        response = await call_next(request)
        log.trace(f'{request.method} {request.url.path} {response.status_code} {int((time.time() - b) * 1000)} ms')
        return response


middlewares = [Middleware(PerformanceMiddleware), Middleware(ExceptionMiddleware)]
