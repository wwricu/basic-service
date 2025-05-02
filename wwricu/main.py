from fastapi import FastAPI

from wwricu.api import api_router
from wwricu.config import Config
from wwricu.domain.constant import CommonConstant
from wwricu.domain.enum import EnvVarEnum
from wwricu.middleware import middlewares
from wwricu.service.common import lifespan


app = FastAPI(
    title=CommonConstant.APP_NAME,
    lifespan=lifespan,
    version=Config.version,
    middleware=middlewares,
    debug=__debug__,
    root_path=EnvVarEnum.ROOT_PATH.get()
)
app.include_router(api_router)
