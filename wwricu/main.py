from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from loguru import logger as log

from wwricu.api import api_router
from wwricu.config import Config
from wwricu.domain.common import CommonConstant
from wwricu.middleware import middlewares


@asynccontextmanager
async def lifespan(fast_api: FastAPI):
    if __debug__:
        log.warning('APP RUNNING ON DEBUG MODE')
    log.info(f'{CommonConstant.APP_TITLE} {CommonConstant.APP_VERSION} Startup')
    fast_api.include_router(api_router)
    log.info(f'listening on {Config.host}:{Config.port}')
    yield
    log.info('THE END')
    await log.complete()


app = FastAPI(
    title=CommonConstant.APP_TITLE,
    version=CommonConstant.APP_VERSION,
    lifespan=lifespan,
    middleware=middlewares
)


def main():
    uvicorn.run(app=Config.app, host=Config.host, port=Config.port, log_level=Config.log_level)
