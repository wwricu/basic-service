import time
from typing import override

from loguru import logger as log
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse


class AspectMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        b = time.time()
        try:
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
        except Exception as e:
            log.trace(f'{request.method} {request.url.path} {int((time.time() - b) * 1000)} ms')
            log.exception(e)
            return JSONResponse(str(e), status_code=500)


# noinspection PyTypeChecker
middlewares = [
    Middleware(AspectMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origin_regex='https?://.*',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
        expose_headers=['*']
    ) if __debug__ else None
]
