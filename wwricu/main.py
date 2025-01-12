import uvicorn
from fastapi import FastAPI

from wwricu.api import api_router
from wwricu.config import Config
from wwricu.domain.common import CommonConstant
from wwricu.service.common import lifespan
from wwricu.middleware import middlewares


app = FastAPI(
    title=CommonConstant.APP_TITLE,
    version='0.0.1',
    lifespan=lifespan,
    middleware=middlewares,
    debug=__debug__
)
app.include_router(api_router)


def main():
    uvicorn.run(app=app, host=Config.host, port=Config.port, log_level=Config.log_level)
