import time
from typing import override

from loguru import logger as log
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AspectMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        b = time.time()
        log.info(f'{request.method} {request.url.path}')
        try:
            response: Response = await call_next(request)
            log.info(f'{request.method} {request.url.path} {response.status_code} {int((time.time() - b) * 1000)} ms')
            return response
        except Exception as e:
            log.exception(e)


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
