from wwricu.api.common import api_router
from wwricu.api.open import open_api
from wwricu.api.post import post_api
from wwricu.api.tag import tag_api


api_router.include_router(open_api)
api_router.include_router(post_api)
api_router.include_router(tag_api)
