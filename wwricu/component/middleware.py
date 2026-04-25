import time
from contextvars import ContextVar
from typing import override

from fastapi import HTTPException, status
from loguru import logger as log
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from wwricu.domain.constant import CommonConstant, HttpHeader

real_ip:ContextVar[str] = ContextVar('real_ip', default='')


class ExceptionMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            log.trace(f'{request.method} {request.url.path} error {e}')
            log.exception(e)
            if isinstance(e, HTTPException):
                raise
            return JSONResponse(CommonConstant.COMMON_ERROR, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerformanceMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        b = time.time()
        ip = (
            request.headers.get(HttpHeader.X_REAL_IP) or
            request.headers.get(HttpHeader.X_FORWARD_FOR, '').split(',')[0].strip() or
            (request.client.host if request.client else '')
        )
        real_ip.set(ip)
        with log.contextualize(real_ip=ip):
            response = await call_next(request)
            log.trace(f'{real_ip.get()} | {request.method} {request.url.path} {response.status_code} {int((time.time() - b) * 1000)} ms')
        return response


middlewares = [
    Middleware(PerformanceMiddleware),
    Middleware(ExceptionMiddleware)
]

if __debug__:
    middlewares.append(
        Middleware(
            CORSMiddleware,
            allow_origin_regex='https?://.*',
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
            expose_headers=['*']
        )
    )
