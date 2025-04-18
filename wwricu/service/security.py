import base64
import hashlib
import hmac
import time
from contextlib import asynccontextmanager

import bcrypt
import pyotp
from fastapi import HTTPException, Request, status
from loguru import logger as log
from sqlalchemy import select

from wwricu.domain.common import LoginRO
from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.entity import SysConfig
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum
from wwricu.config import AdminConfig, Config
from wwricu.service.cache import cache
from wwricu.service.database import session


@asynccontextmanager
async def try_login_lock():
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


async def admin_login(login_request: LoginRO) -> bool:
    if __debug__:
        return True

    stmt = select(SysConfig).where(SysConfig.key == ConfigKeyEnum.TOTP_ENFORCE).where(SysConfig.deleted == False)
    enforce = await session.scalar(stmt)
    stmt = select(SysConfig).where(SysConfig.key == ConfigKeyEnum.TOTP_SECRET).where(SysConfig.deleted == False)
    secret = await session.scalar(stmt)
    if enforce is not None and secret is not None and secret.value is not None:
        totp = pyotp.TOTP(secret.value)
        pyotp.random_base32()
        if not totp.verify(login_request.totp, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_TOTP)

    username, password = AdminConfig.username, AdminConfig.password
    if username_config := await session.scalar(select(SysConfig).where(SysConfig.key == ConfigKeyEnum.USERNAME)):
        username = username_config.value
    if password_config := await session.scalar(select(SysConfig).where(SysConfig.key == ConfigKeyEnum.PASSWORD)):
        password = password_config.value
    if login_request.username != username:
        return False
    return bcrypt.checkpw(login_request.password.encode(), base64.b64decode(password))


async def admin_only(request: Request):
    session_id = request.cookies.get(CommonConstant.SESSION_ID)
    cookie_sign = request.cookies.get(CommonConstant.COOKIE_SIGN)
    if await validate_cookie(session_id, cookie_sign) is not True:
        log.warning(f'Unauthorized access to {request.url.path}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.NOT_AUTHORIZED)


def hmac_sign(plain: str):
    return hmac.new(secure_key, plain.encode(Config.encoding), hashlib.sha256).hexdigest()


async def validate_cookie(session_id: str, cookie_sign: str) -> bool:
    if __debug__ is True:
        return True
    if session_id is None or cookie_sign is None or not isinstance(issue_time := await cache.get(session_id), int):
        return False
    if 0 <= int(time.time()) - issue_time < CommonConstant.EXPIRE_TIME and hmac_sign(session_id) == cookie_sign:
        return True
    log.warning(f'Invalid cookie session={session_id} issue_time={issue_time} sign={cookie_sign}')
    return False


secure_key = base64.b64decode(AdminConfig.secure_key)
