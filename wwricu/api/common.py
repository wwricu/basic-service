from fastapi import APIRouter, Depends, Request, Response

from wwricu.component.cache import sys_cache
from wwricu.domain.common import LoginRO
from wwricu.domain.constant import CommonConstant
from wwricu.service import security_service

common_api = APIRouter(tags=['Common API'])


@common_api.post('/login', dependencies=[Depends(security_service.login_limiter)], response_model=None)
async def login_api(login_request: LoginRO, request: Request, response: Response):
    if not await security_service.authenticate_2fa(login_request, request, response):
        await security_service.authenticate(login_request, response)


@common_api.get('/logout', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def logout_api(request: Request, response: Response):
    if (session_id := request.cookies.get(CommonConstant.SESSION_ID)) is None:
        return
    response.delete_cookie(CommonConstant.SESSION_ID)
    response.delete_cookie(CommonConstant.COOKIE_SIGN)
    await sys_cache.delete(session_id)


@common_api.get('/info', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def info_api():
    return
