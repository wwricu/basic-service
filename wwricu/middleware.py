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
        try:
            log.info('{method} {path} {params}'.format(
                method=request.method,
                path=request.url.path,
                params='' if 'multipart/form-data' in request.headers.get('Content-Type', '') else await request.body(),
            ))
            response: Response = await call_next(request)
            log.info('{method} {path} {status_code} {time} ms'.format(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                time=int((time.time() - b) * 1000),
            ))
            return response
        except Exception as e:
            log.error(f'{request.method} {request.url.path} {int((time.time() - b) * 1000)} ms')
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
