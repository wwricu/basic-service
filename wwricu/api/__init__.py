from fastapi import APIRouter

from wwricu.api.common import common_api, image_api
from wwricu.api.manage import manage_api
from wwricu.api.open import open_api
from wwricu.api.post import post_api
from wwricu.api.tag import tag_api

# Reachable with nothing but a URL: the blog's own endpoints and the resource edge images.
public_api = APIRouter()
public_api.include_router(open_api)
public_api.include_router(image_api)

# The group the edge publishes only for the admin app. The split is by URL at the edge; the
# service itself does not authenticate the caller here - the session cookie behind these
# handlers does.
privileged_api = APIRouter()
privileged_api.include_router(common_api)
privileged_api.include_router(manage_api)
privileged_api.include_router(post_api)
privileged_api.include_router(tag_api)

api_router = APIRouter()
api_router.include_router(public_api)
api_router.include_router(privileged_api)

__all__ = ['api_router']
