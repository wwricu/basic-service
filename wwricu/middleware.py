import time
from typing import override

from loguru import logger as log
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request


class AspectMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        begin = time.time()
        try:
            return await call_next(request)
        finally:
            log.info(f'{request.method} {request.url.path} {int((time.time() - begin) * 1000)} ms')


# noinspection PyTypeChecker
middlewares = [Middleware(AspectMiddleware)]


if __debug__ is True:
    # noinspection PyTypeChecker
    middlewares.append(Middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
        expose_headers=['*']
    ))
