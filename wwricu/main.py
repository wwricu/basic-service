import os

import uvicorn
from fastapi import FastAPI

from wwricu.api import api_router
from wwricu.config import Config
from wwricu.domain.constant import CommonConstant
from wwricu.middleware import middlewares
from wwricu.service.common import lifespan


app = FastAPI(
    title=CommonConstant.APP_NAME,
    lifespan=lifespan,
    middleware=middlewares,
    debug=__debug__,
    root_path=os.getenv(CommonConstant.ROOT_PATH, '/')
)
app.include_router(api_router)


def main():
    uvicorn.run(app=app, host=Config.host, port=Config.port, log_level=Config.log_level, access_log=False)
