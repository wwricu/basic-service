import base64
import hashlib
import hmac
import time
from contextlib import asynccontextmanager

import bcrypt
import pyotp
from fastapi import HTTPException, Request, Response, status
from loguru import logger as log

from wwricu.domain.common import LoginRO
from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum
from wwricu.config import AdminConfig, Config
from wwricu.component.cache import cache
from wwricu.service.manage import get_sys_config


@asynccontextmanager
async def login_lock():
    if await cache.get(CacheKeyEnum.LOGIN_LOCK) is not None:
        log.warning('LOGIN FORBIDDEN')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='LOGIN FORBIDDEN')
    try:
        yield
        await cache.delete(CacheKeyEnum.LOGIN_LOCK)
        await cache.delete(CacheKeyEnum.LOGIN_RETRIES)
    except Exception as e:
        if (retries := await cache.get(CacheKeyEnum.LOGIN_RETRIES)) is None:
            retries = 0
        log.warning(f'Login failed {retries=}')
        if retries >= 2:
            await cache.set(CacheKeyEnum.LOGIN_LOCK, True, 600)
            await cache.delete(CacheKeyEnum.LOGIN_RETRIES)
        else:
            await cache.set(CacheKeyEnum.LOGIN_RETRIES, retries + 1, 300)
        raise e


async def verify_credentials(login_request: LoginRO) -> bool:
    username, password = await get_sys_config(ConfigKeyEnum.USERNAME), await get_sys_config(ConfigKeyEnum.PASSWORD)
    if not username:
        username = AdminConfig.username
    if not password:
        password = AdminConfig.password
    if login_request.username != username:
        return False
    return bcrypt.checkpw(login_request.password.encode(), base64.b64decode(password))


async def authenticate_admin(login_request: LoginRO):
    async with login_lock():
        if not await verify_credentials(login_request):
            log.warning(f'{login_request.username} login failure')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)

    enforce = await get_sys_config(ConfigKeyEnum.TOTP_ENFORCE)
    secret = await get_sys_config(ConfigKeyEnum.TOTP_SECRET)
    if enforce is None or secret is None:
        return
    if not login_request.totp:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=HttpErrorDetail.NEED_TOTP)
    totp_client = pyotp.TOTP(secret)
    async with login_lock():
        if not totp_client.verify(login_request.totp, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_TOTP)


async def require_admin(request: Request, response: Response):
    if __debug__:
        return

    session_id = request.cookies.get(CommonConstant.SESSION_ID)
    cookie_sign = request.cookies.get(CommonConstant.COOKIE_SIGN)
    if session_id is None or cookie_sign is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.NOT_AUTHORIZED)

    if not await validate_cookie(session_id, cookie_sign):
        log.warning(f'Unauthorized access to {request.url.path}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.NOT_AUTHORIZED)
    if not (cookie_time := await cache.get(session_id)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.LOGIN_TIMEOUT)

    if (now := int(time.time())) >= cookie_time + CommonConstant.ONE_DAY_SECONDS:
        log.warning(f'{session_id} renew')
        await cache.set(session_id, now, CommonConstant.COOKIE_MAX_AGE)
        set_auth_cookies(session_id, response)


def hmac_sign(plain: str) -> str:
    secure_key = base64.b64decode(AdminConfig.secure_key)
    return hmac.new(secure_key, plain.encode(Config.encoding), hashlib.sha256).hexdigest()


async def validate_cookie(session_id: str, cookie_sign: str) -> bool:
    if not isinstance(issue_time := await cache.get(session_id), int):
        return False
    if 0 <= int(time.time()) - issue_time < CommonConstant.COOKIE_MAX_AGE and hmac_sign(session_id) == cookie_sign:
        return True
    log.warning(f'Invalid cookie session_id={session_id} issue_time={issue_time} sign={cookie_sign}')
    return False


def set_auth_cookies(session_id: str, response: Response):
    response.delete_cookie(CommonConstant.SESSION_ID)
    response.delete_cookie(CommonConstant.COOKIE_SIGN)
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
