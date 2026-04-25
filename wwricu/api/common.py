import time
import uuid

from fastapi import APIRouter, Depends, Request, Response

from wwricu.component.cache import sys_cache
from wwricu.domain.common import LoginRO
from wwricu.domain.constant import CommonConstant
from wwricu.domain.enum import CacheKeyEnum
from wwricu.service import security_service

common_api = APIRouter(tags=['Common API'])


@common_api.post('/login', response_model=None, dependencies=[Depends(security_service.rate_limit)])
async def login_api(login_request: LoginRO, response: Response):
    await security_service.authenticate_admin(login_request)
    session_id = uuid.uuid4().hex
    await sys_cache.set(session_id, int(time.time()), CommonConstant.COOKIE_MAX_AGE)
    await sys_cache.delete(CacheKeyEnum.LOGIN_LOCK)
    security_service.set_auth_cookies(session_id, response)


@common_api.get('/logout', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def logout_api(request: Request, response: Response):
    if (session_id := request.cookies.get(CommonConstant.SESSION_ID)) is None:
        return
    await sys_cache.delete(session_id)
    response.delete_cookie(CommonConstant.SESSION_ID)
    response.delete_cookie(CommonConstant.COOKIE_SIGN)


@common_api.get('/info', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def info_api():
    return
