from fastapi import APIRouter, Depends

from wwricu.api.common import common_api, image_api
from wwricu.api.manage import manage_api
from wwricu.api.open import open_api
from wwricu.api.post import post_api
from wwricu.api.tag import tag_api
from wwricu.service import security_service

# Reachable with nothing but a URL: the blog's own endpoints and the resource edge images.
public_api = APIRouter()
public_api.include_router(open_api)
public_api.include_router(image_api)

# The group the edge publishes only for the admin app. The split is by URL at the edge; the
# session cookie behind these handlers authenticates the caller.
privileged_api = APIRouter(dependencies=[Depends(security_service.verify_origin)])
privileged_api.include_router(common_api)
privileged_api.include_router(manage_api)
privileged_api.include_router(post_api)
privileged_api.include_router(tag_api)

api_router = APIRouter()
api_router.include_router(public_api)
api_router.include_router(privileged_api)

__all__ = ['api_router']
