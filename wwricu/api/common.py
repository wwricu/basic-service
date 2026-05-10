from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse

from wwricu.component.cache import image_cache
from wwricu.component.storage import oss_public
from wwricu.domain.common import LoginRO, LoginVO
from wwricu.domain.constant import TimeConst
from wwricu.service import security_service

common_api = APIRouter(tags=['Common API'])


@common_api.post('/login', dependencies=[Depends(security_service.login_limiter)], response_model=LoginVO)
async def login_api(login_request: LoginRO, request: Request, response: Response):
    return await security_service.authenticate(login_request, request, response)


@common_api.get('/logout', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def logout_api(request: Request, response: Response):
    await security_service.logout(request, response)


@common_api.get('/info', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def info_api():
    return


@common_api.get('/image/{key:path}', dependencies=[Depends(security_service.image_limiter)])
async def image_api(key: str):
    if url := await image_cache.get(key):
        return RedirectResponse(url)
    url = oss_public.generate_presigned_url(key, expires=TimeConst.ONE_DAY_SECONDS)
    await image_cache.set(key, url, second=TimeConst.ONE_DAY_SECONDS - TimeConst.ONE_HOUR_SECONDS)
    return RedirectResponse(url)
