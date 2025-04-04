import base64
import hashlib
import hmac
import time
from contextlib import asynccontextmanager

import bcrypt
from fastapi import HTTPException, Request, status
from loguru import logger as log
from sqlalchemy import select

from domain.entity import SysConfig
from wwricu.domain.constant import CommonConstant, HttpErrorDetail
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


async def admin_login(username: str, password: str) -> bool:
    if __debug__:
        return True
    sys_username = AdminConfig.username
    sys_password = AdminConfig.password
    if username_config := await session.scalar(select(SysConfig).where(SysConfig.key == ConfigKeyEnum.USERNAME)):
        sys_username = username_config.value
    if password_config := await session.scalar(select(SysConfig).where(SysConfig.key == ConfigKeyEnum.PASSWORD)):
        sys_password = password_config.value
    if username != sys_username:
        return False
    return bcrypt.checkpw(password.encode(), base64.b64decode(sys_password))


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

secure_key = base64.b64decode(AdminConfig.secure_key.encode(Config.encoding))
