from fastapi import APIRouter, Depends

from wwricu.api.common import common_api, image_api
from wwricu.api.manage import manage_api
from wwricu.api.open import open_api
from wwricu.api.post import post_api
from wwricu.api.tag import tag_api
from wwricu.service.security import require_internal_token

# Reachable with nothing but a URL: the blog's own endpoints and the resource edge images.
public_api = APIRouter()
public_api.include_router(open_api)
public_api.include_router(image_api)

# Only Caddy knows the token, so the blog stack - which calls this service directly on the
# docker network - cannot reach these routes even if it builds the URL by mistake.
privileged_api = APIRouter(dependencies=[Depends(require_internal_token)])
privileged_api.include_router(common_api)
privileged_api.include_router(manage_api)
privileged_api.include_router(post_api)
privileged_api.include_router(tag_api)

api_router = APIRouter()
api_router.include_router(public_api)
api_router.include_router(privileged_api)

__all__ = ['api_router']
