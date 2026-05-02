from fastapi import FastAPI

from wwricu.api import api_router
from wwricu.component.middleware import middlewares
from wwricu.config import env
from wwricu.domain.constant import CommonConstant
from wwricu.service.common import lifespan


app = FastAPI(
    title=CommonConstant.APP_NAME,
    lifespan=lifespan,
    middleware=middlewares,
    debug=__debug__,
    version=env.VERSION,
    root_path=env.ROOT_PATH
)
app.include_router(api_router)
