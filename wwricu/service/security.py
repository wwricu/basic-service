import asyncio
import base64
import functools
import hashlib
import hmac
import time
import uuid
from typing import Callable

import bcrypt
import pyotp
from fastapi import HTTPException, Request, Response, status
from loguru import logger as log

from wwricu.component.middleware import real_ip
from wwricu.domain.common import LoginRO
from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.enum import ConfigKeyEnum
from wwricu.config import AdminConfig, Config
from wwricu.component.cache import sys_cache
from wwricu.component.token_bucket import TokenBucketLimiter
from wwricu.service.manage import get_config


async def login_limiter():
    if not await ip_login_limiter.allow(real_ip.get()):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=HttpErrorDetail.TOO_MANY_REQUESTS)
    if not await global_login_limiter.allow(CommonConstant.GLOBAL_TOKEN_BUCKET_ID):
        log.warning('Global login rate limit exceeded')
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=HttpErrorDetail.TOO_MANY_REQUESTS)


def throttle(concurrent: int, timeout: float = 2.0):
    sem = asyncio.Semaphore(concurrent)
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                await asyncio.wait_for(sem.acquire(), timeout=timeout)
            except asyncio.TimeoutError:
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail=HttpErrorDetail.TOO_MANY_REQUESTS)
            try:
                return await func(*args, **kwargs)
            finally:
                sem.release()
        return wrapper
    return decorator


@throttle(concurrent=1)
async def verify_credentials(request: LoginRO) -> bool:
    username, password = await get_config(ConfigKeyEnum.USERNAME), await get_config(ConfigKeyEnum.PASSWORD)
    if not username:
        username = AdminConfig.username
    if not password:
        password = AdminConfig.password
    return await asyncio.to_thread(bcrypt.checkpw, request.password.encode(), base64.b64decode(password)) and request.username == username


async def authenticate_2fa(login_request: LoginRO, request: Request, response: Response) -> bool:
    if not (session_2fa_id := request.cookies.get(CommonConstant.SESSION_ID_2FA)):
        return False
    if (await sys_cache.get(session_2fa_id)) is None:
        return False

    enforce = await get_config(ConfigKeyEnum.TOTP_ENFORCE)
    secret = await get_config(ConfigKeyEnum.TOTP_SECRET)
    if not enforce or secret is None:
        await sys_cache.delete(session_2fa_id)
        response.delete_cookie(CommonConstant.SESSION_ID_2FA)
        return False
    if login_request.totp is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.NEED_TOTP)

    if not pyotp.TOTP(secret).verify(login_request.totp, valid_window=1):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_TOTP)
    await sys_cache.delete(session_2fa_id)
    response.delete_cookie(CommonConstant.SESSION_ID_2FA)
    await login(session_2fa_id, response)
    return True


async def authenticate(login_request: LoginRO, response: Response):
    if not await verify_credentials(login_request):
        log.warning(f'{login_request.username} login failure')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)

    if not await get_config(ConfigKeyEnum.TOTP_ENFORCE):
        await login(uuid.uuid4().hex, response)
        return

    session_id = uuid.uuid4().hex
    await sys_cache.set(session_id, True, 300)
    response.set_cookie(CommonConstant.SESSION_ID_2FA, session_id, max_age=300, secure=True, httponly=True, samesite='lax')
    response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT


async def require_admin(request: Request, response: Response):
    if __debug__:
        return

    session_id = request.cookies.get(CommonConstant.SESSION_ID)
    cookie_sign = request.cookies.get(CommonConstant.COOKIE_SIGN)
    if session_id is None or cookie_sign is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.NOT_AUTHORIZED)

    if (
        not isinstance(issue_time := await sys_cache.get(session_id), int) or
        issue_time < 0 or
        int(time.time()) - issue_time >= CommonConstant.COOKIE_MAX_AGE or
        hmac_sign(session_id) != cookie_sign
    ):
        log.warning(f'Unauthorized access to {request.url.path}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.NOT_AUTHORIZED)

    if issue_time + CommonConstant.ONE_DAY_SECONDS <= int(time.time()):
        log.warning(f'{session_id} renew')
        await login(session_id, response)


def hmac_sign(plain: str) -> str:
    secure_key = base64.b64decode(AdminConfig.secure_key)
    return hmac.new(secure_key, plain.encode(Config.encoding), hashlib.sha256).hexdigest()


async def login(session_id: str, response: Response):
    await sys_cache.set(session_id, int(time.time()), CommonConstant.COOKIE_MAX_AGE)
    response.set_cookie(CommonConstant.SESSION_ID, session_id, CommonConstant.COOKIE_MAX_AGE, secure=True, httponly=True, samesite='lax')
    response.set_cookie(CommonConstant.COOKIE_SIGN, hmac_sign(session_id), CommonConstant.COOKIE_MAX_AGE, secure=True, httponly=True, samesite='lax')


# 0.5 QPS for a single IP, 3 QPS for global;
# bcrypt run for ~290ms/750ms on 1C1G with light/heavy load
ip_login_limiter = TokenBucketLimiter(name='ip', capacity=30, refill_speed=0.5)
global_login_limiter = TokenBucketLimiter(name='global', capacity=120, refill_speed=2)
