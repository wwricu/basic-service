from fastapi import APIRouter, Depends

from wwricu.api.common import common_api
from wwricu.api.manage import manage_api
from wwricu.api.open import open_api
from wwricu.api.post import post_api
from wwricu.api.tag import tag_api
from wwricu.service.database import open_session


api_router = APIRouter(dependencies=[Depends(open_session)])
api_router.include_router(common_api)
api_router.include_router(manage_api)
api_router.include_router(open_api)
api_router.include_router(post_api)
api_router.include_router(tag_api)
