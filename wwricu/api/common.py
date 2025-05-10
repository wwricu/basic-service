import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from loguru import logger as log

from wwricu.config import AdminConfig
from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum
from wwricu.domain.common import LoginRO
from wwricu.service.cache import cache
from wwricu.service.manage import get_config
from wwricu.service.security import admin_only, hmac_sign, validate_cookie, admin_login, try_login_lock

common_api = APIRouter(tags=['Common API'])


@common_api.post('/login', response_model=None)
async def login(login_request: LoginRO, response: Response):
    async with try_login_lock():
        if await admin_login(login_request) is not True:
            log.warning(f'{login_request.username} login failure')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)
    if (session_id := await cache.get(login_request.username)) is None:
        session_id = uuid.uuid4().hex
        await cache.set(login_request.username, session_id, CommonConstant.COOKIE_TIMEOUT_SECOND)
    cookie_sign = hmac_sign(session_id)
    await cache.set(session_id, int(time.time()), CommonConstant.COOKIE_TIMEOUT_SECOND)
    await cache.delete(CacheKeyEnum.LOGIN_LOCK)
    response.set_cookie(CommonConstant.SESSION_ID, session_id, secure=True, httponly=True, samesite='lax')
    response.set_cookie(CommonConstant.COOKIE_SIGN, cookie_sign, secure=True, httponly=True, samesite='lax')


@common_api.get('/logout', dependencies=[Depends(admin_only)], response_model=None)
async def logout(request: Request, response: Response):
    if (session_id := request.cookies.get(CommonConstant.SESSION_ID)) is None:
        return
    await cache.delete(session_id)
    await cache.delete(AdminConfig.username)
    response.delete_cookie(CommonConstant.SESSION_ID)
    response.delete_cookie(CommonConstant.COOKIE_SIGN)


@common_api.get('/info', response_model=bool)
async def info(request: Request) -> bool:
    session_id = request.cookies.get(CommonConstant.SESSION_ID)
    cookie_sign = request.cookies.get(CommonConstant.COOKIE_SIGN)
    if valid := await validate_cookie(session_id, cookie_sign):
        await cache.set(session_id, int(time.time()), CommonConstant.COOKIE_TIMEOUT_SECOND)
    return valid


@common_api.get('/totp', response_model=bool)
async def totp() -> bool:
    return await get_config(ConfigKeyEnum.TOTP_ENFORCE) == str(True)
