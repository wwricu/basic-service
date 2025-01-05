import time
from typing import override

from loguru import logger as log
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from wwricu.service.common import validate_cookie, admin
from wwricu.domain.common import CommonConstant


class PerformanceMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        begin = time.time()
        try:
            return await call_next(request)
        finally:
            log.info(f'{request.method} {request.url.path} {(int((time.time() - begin) * 1000))} ms')


class AspectMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        log.info(f'{request.method} {request.url.path}')
        try:
            return await call_next(request)
        except Exception as e:
            log.exception(e)


class AuthMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        session_id = request.cookies.get(CommonConstant.SESSION_ID)
        cookie_sign = request.cookies.get(CommonConstant.COOKIE_SIGN)
        if await validate_cookie(session_id, cookie_sign):
            admin.set(True)
        try:
            return await call_next(request)
        finally:
            admin.set(False)


# noinspection PyTypeChecker
middlewares = [
    Middleware(AspectMiddleware),
    Middleware(AuthMiddleware)
]


if __debug__ is True:
    # noinspection PyTypeChecker
    middlewares.insert(0, Middleware(PerformanceMiddleware))
    # noinspection PyTypeChecker
    middlewares.append(Middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
        expose_headers=['*']
    ))
