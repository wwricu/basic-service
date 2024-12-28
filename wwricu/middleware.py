import time
from typing import override

from loguru import logger as log
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from wwricu.service.common import admin_user, hmac_verify
from wwricu.domain.common import CommonConstant
from wwricu.service.cache import cache_get


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
        log.info(f'{request.method} {request.url.path} {await request.json()}')
        try:
            return await call_next(request)
        except Exception as e:
            log.exception(e)


class AuthMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        session_id = request.cookies.get(CommonConstant.SESSION_ID)
        session_sign = request.cookies.get(CommonConstant.SESSION_SIGN)
        issue_time = cache_get(session_id)
        if (
            __debug__ is True or
            isinstance(issue_time, int) and
            0 < int(time.time()) - issue_time < CommonConstant.EXPIRE_TIME and
            hmac_verify(session_id, session_sign) is True
        ):
            async with admin_user():
                return await call_next(request)


# noinspection PyTypeChecker
middlewares = [
    Middleware(AspectMiddleware),
    Middleware(AuthMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
        expose_headers=['*']
    )
]


if __debug__ is True:
    # noinspection PyTypeChecker
    middlewares.insert(0, Middleware(PerformanceMiddleware))
