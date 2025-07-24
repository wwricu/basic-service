from fastapi import FastAPI, Depends

from wwricu.api import api_router
from wwricu.domain.constant import CommonConstant
from wwricu.domain.enum import EnvVarEnum
from wwricu.middleware import middlewares
from wwricu.service.common import lifespan
from wwricu.service.database import open_session


app = FastAPI(
    title=CommonConstant.APP_NAME,
    lifespan=lifespan,
    middleware=middlewares,
    dependencies=[Depends(open_session)],
    debug=__debug__,
    root_path=EnvVarEnum.ROOT_PATH.get()
)
app.include_router(api_router)
