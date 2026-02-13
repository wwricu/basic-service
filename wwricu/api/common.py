import time
import uuid

import pyotp
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from loguru import logger as log

from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum
from wwricu.domain.common import LoginRO
from wwricu.service.cache import cache
from wwricu.service.manage import get_config
from wwricu.service.security import admin_only, hmac_sign, admin_login, try_login_lock

common_api = APIRouter(tags=['Common API'])


@common_api.post('/login', response_model=None)
async def login(login_request: LoginRO, response: Response):
    async with try_login_lock():
        if not await admin_login(login_request):
            log.warning(f'{login_request.username} login failure')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)

    enforce = await get_config(ConfigKeyEnum.TOTP_ENFORCE)
    secret = await get_config(ConfigKeyEnum.TOTP_SECRET)
    if enforce is not None and secret is not None:
        if not login_request.totp:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=HttpErrorDetail.NEED_TOTP)
        totp_client = pyotp.TOTP(secret)
        async with try_login_lock():
            if not totp_client.verify(login_request.totp, valid_window=1):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_TOTP)

    session_id = uuid.uuid4().hex
    await cache.set(session_id, int(time.time()), CommonConstant.COOKIE_MAX_AGE)
    await cache.delete(CacheKeyEnum.LOGIN_LOCK)

    response.set_cookie(
        CommonConstant.SESSION_ID,
        session_id,
        max_age=CommonConstant.COOKIE_MAX_AGE,
        secure=True,
        httponly=True,
        samesite='lax'
    )
    response.set_cookie(
        CommonConstant.COOKIE_SIGN,
        hmac_sign(session_id),
        max_age=CommonConstant.COOKIE_MAX_AGE,
        secure=True,
        httponly=True,
        samesite='lax'
    )


@common_api.get('/logout', dependencies=[Depends(admin_only)], response_model=None)
async def logout(request: Request, response: Response):
    if (session_id := request.cookies.get(CommonConstant.SESSION_ID)) is None:
        return
    await cache.delete(session_id)
    response.delete_cookie(CommonConstant.SESSION_ID)
    response.delete_cookie(CommonConstant.COOKIE_SIGN)


@common_api.get('/info', dependencies=[Depends(admin_only)], response_model=None)
async def info():
    return
