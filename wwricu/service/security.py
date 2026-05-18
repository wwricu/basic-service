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

import wwricu.service.manage as manage_service
from wwricu.component.cache import sys_cache
from wwricu.component.middleware import real_ip
from wwricu.component.token_bucket import default_bucket, login_ip_bucket
from wwricu.config import app_config
from wwricu.domain.common import LoginRO, LoginVO
from wwricu.domain.constant import CommonConst, HttpErrorDetail, TimeConst
from wwricu.domain.enum import ConfigKeyEnum


async def login_limiter():
    if not await login_ip_bucket.cost(real_ip.get(), app_config.security.login_ip_span / app_config.security.login_ip_times):
        log.warning(f'{real_ip.get()} exceeded login rate limit')
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)
    yield
    await login_ip_bucket.reset(real_ip.get())


async def image_limiter():
    if not await default_bucket.allow(CommonConst.IMAGE_IP_BUCKET.format(ip=real_ip.get()), app_config.security.image_ip_qps):
        log.warning(f'{real_ip.get()} exceeded image rate limit')
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)


async def open_limiter():
    if not await default_bucket.allow(CommonConst.OPEN_IP_BUCKET.format(ip=real_ip.get()), app_config.security.open_ip_qps):
        log.warning(f'{real_ip.get()} exceeded open rate limit')
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS)


async def authenticate(login_request: LoginRO, request: Request, response: Response) -> LoginVO:
    session_id = uuid.uuid4().hex
    session_2fa_id = request.cookies.get(CommonConst.SESSION_ID_2FA)

    secret = await manage_service.get_config(ConfigKeyEnum.TOTP_SECRET)
    enforce = await manage_service.get_config(ConfigKeyEnum.TOTP_ENFORCE)

    if session_2fa_id and (not enforce or not login_request.totp):
        await sys_cache.delete(session_2fa_id)
        response.delete_cookie(CommonConst.SESSION_ID_2FA)
    elif session_2fa_id and enforce and secret and login_request.totp and await sys_cache.get(session_2fa_id):
        if not pyotp.TOTP(secret).verify(login_request.totp, valid_window=1):
            log.warning(f'{login_request.username} wrong totp')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_TOTP)
        await sys_cache.delete(session_2fa_id)
        response.delete_cookie(CommonConst.SESSION_ID_2FA)
        await login(session_id, response)
        return LoginVO()

    if not await verify_credentials(login_request):
        log.warning(f'{login_request.username} login failure')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)

    if await manage_service.get_config(ConfigKeyEnum.TOTP_ENFORCE):
        await sys_cache.set(session_id, True, TimeConst.TOTP_EXPIRATION)
        response.set_cookie(CommonConst.SESSION_ID_2FA, session_id, max_age=TimeConst.TOTP_EXPIRATION, secure=True, httponly=True, samesite='lax')
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return LoginVO(detail=HttpErrorDetail.NEED_TOTP)

    await login(session_id, response)
    return LoginVO()


async def require_admin(request: Request, response: Response):
    if not await is_admin(request, response):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def is_admin(request: Request, response: Response) -> bool:
    if __debug__:
        return True

    session_id = request.cookies.get(CommonConst.SESSION_ID)
    cookie_sign = request.cookies.get(CommonConst.COOKIE_SIGN)
    if session_id is None or cookie_sign is None:
        return False

    if (
        not isinstance(issue_time := await sys_cache.get(session_id), int) or
        issue_time < 0 or
        int(time.time()) - issue_time >= TimeConst.COOKIE_MAX_AGE or
        hmac_sign(session_id) != cookie_sign
    ):
        log.warning(f'Unauthorized access to {request.url.path}')
        return False

    if issue_time + TimeConst.ONE_DAY_SECONDS < int(time.time()):
        log.info(f'{session_id} renew')
        await login(session_id, response)
    return True


def hmac_sign(plain: str) -> str:
    return hmac.new(base64.b64decode(app_config.security.secret_key), plain.encode(), hashlib.sha256).hexdigest()


async def login(session_id: str, response: Response):
    await sys_cache.set(session_id, int(time.time()), TimeConst.COOKIE_MAX_AGE)
    response.set_cookie(CommonConst.SESSION_ID, session_id, TimeConst.COOKIE_MAX_AGE, secure=True, httponly=True, samesite='lax')
    response.set_cookie(CommonConst.COOKIE_SIGN, hmac_sign(session_id), TimeConst.COOKIE_MAX_AGE, secure=True, httponly=True, samesite='lax')


def throttle(concurrent: int, timeout: float):
    sem = asyncio.Semaphore(concurrent)
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                await asyncio.wait_for(sem.acquire(), timeout=timeout)
            except asyncio.TimeoutError:
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS)
            try:
                return await func(*args, **kwargs)
            finally:
                sem.release()
        return wrapper
    return decorator


@throttle(concurrent=1, timeout=2.0)
async def verify_credentials(request: LoginRO) -> bool:
    username = await manage_service.get_config(ConfigKeyEnum.USERNAME)
    password = await manage_service.get_config(ConfigKeyEnum.PASSWORD)
    if not username:
        username = app_config.security.username
    if not password:
        password = app_config.security.password
    return await asyncio.to_thread(bcrypt.checkpw, request.password.encode(), base64.b64decode(password)) and request.username == username


async def logout(request: Request, response: Response):
    if (session_id := request.cookies.get(CommonConst.SESSION_ID)) is None:
        return
    response.delete_cookie(CommonConst.SESSION_ID)
    response.delete_cookie(CommonConst.COOKIE_SIGN)
    await sys_cache.delete(session_id)
