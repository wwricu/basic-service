from fastapi import FastAPI

from wwricu.api import api_router
from wwricu.component.middleware import middlewares
from wwricu.config import env
from wwricu.service.common import lifespan


app = FastAPI(
    title=env.BASE_DOMAIN,
    lifespan=lifespan,
    middleware=middlewares,
    docs_url=None,
    redoc_url=None,
    debug=env.is_dev
)

app.include_router(api_router)
