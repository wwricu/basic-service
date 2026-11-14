from fastapi import APIRouter, Depends

from wwricu.api.common import common_api, image_api
from wwricu.api.manage import manage_api
from wwricu.api.open import open_api
from wwricu.api.post import post_api
from wwricu.api.tag import tag_api
from wwricu.service import security_service

admin_api = APIRouter(dependencies=[Depends(security_service.verify_origin)])
admin_api.include_router(common_api)
admin_api.include_router(manage_api)
admin_api.include_router(post_api)
admin_api.include_router(tag_api)

api_router = APIRouter()
api_router.include_router(open_api)
api_router.include_router(image_api)
api_router.include_router(admin_api)

__all__ = ['api_router']
