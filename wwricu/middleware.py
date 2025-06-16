import time
from typing import override

from loguru import logger as log
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class ExceptionMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        log.info('exception middleware')
        try:
            return await call_next(request)
        except Exception as e:
            log.trace(f'{request.method} {request.url.path} error {e}')
            log.exception(e)
            return JSONResponse(str(e), status_code=500)


class PerformanceMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        log.info('performance middleware')
        b = time.time()
        log.trace('{method} {path} {params}'.format(
            method=request.method,
            path=request.url.path,
            params='' if 'multipart/form-data' in request.headers.get('Content-Type', '') else await request.body(),
        ))
        response = await call_next(request)
        log.trace('{method} {path} {status_code} {time} ms'.format(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            time=int((time.time() - b) * 1000),
        ))
        return response


middlewares = [
    Middleware(ExceptionMiddleware),
    Middleware(PerformanceMiddleware)
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
