import asyncio
import base64
import hashlib
import hmac
import uuid
from datetime import datetime

import bcrypt
import pyotp
from fastapi import HTTPException, Request, Response, status
from loguru import logger as log

import wwricu.service.manage as manage_service
from wwricu.component.cache import session_cache, sys_cache
from wwricu.config import app_config, env
from wwricu.domain.common import LoginRO, LoginVO, SessionVO
from wwricu.domain.constant import CommonConst, HttpErrorDetail, TimeConst
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum


async def authenticate(login_request: LoginRO, request: Request, response: Response) -> LoginVO:
    session_id = uuid.uuid4().hex
    session_2fa_id = request.cookies.get(CommonConst.SESSION_ID_2FA)

    secret = await manage_service.get_config(ConfigKeyEnum.TOTP_SECRET)
    enforce = await manage_service.get_config(ConfigKeyEnum.TOTP_ENFORCE)

    if session_2fa_id and (enforce is None or not login_request.totp):
        await sys_cache.delete(session_2fa_id)
        response.delete_cookie(CommonConst.SESSION_ID_2FA)
    elif session_2fa_id and enforce is not None and secret and login_request.totp and await sys_cache.get(session_2fa_id):
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

    if enforce is not None:
        await sys_cache.set(session_id, True, TimeConst.TOTP_EXPIRATION)
        response.set_cookie(CommonConst.SESSION_ID_2FA, session_id, max_age=TimeConst.TOTP_EXPIRATION, secure=True, httponly=True, samesite='strict')
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return LoginVO(detail=HttpErrorDetail.NEED_TOTP)

    await login(session_id, response)
    return LoginVO()


async def require_admin(request: Request, response: Response):
    if not await is_admin(request, response):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def is_admin(request: Request, response: Response) -> bool:
    if env.is_dev:
        return True

    session_id = request.cookies.get(CommonConst.SESSION_ID)
    cookie_sign = request.cookies.get(CommonConst.COOKIE_SIGN)
    if session_id is None or cookie_sign is None:
        return False

    session: SessionVO | None = await session_cache.get(session_id)
    if session is None or not hmac.compare_digest(hmac_sign(session_id), cookie_sign):
        log.warning(f'Unauthorized access to {request.url.path}')
        return False

    now = datetime.now()
    session.last_active = now
    session.ua = request.headers.get('user-agent', '')
    if session.issue_time + TimeConst.ONE_DAY_SECONDS < now.timestamp():
        session.issue_time = int(now.timestamp())
        await login(session_id, response)
    return True


def hmac_sign(plain: str) -> str:
    return hmac.new(base64.b64decode(app_config.security.secret_key), plain.encode(), hashlib.sha256).hexdigest()


async def login(session_id: str, response: Response):
    # reuse the stored record so fields the caller just refreshed survive renewal
    session: SessionVO = await session_cache.get(session_id) or SessionVO(id=session_id)
    await session_cache.set(session_id, session, TimeConst.COOKIE_MAX_AGE)
    login_sessions = await session_cache.get(CacheKeyEnum.SESSION_IDS) or []
    if session_id not in login_sessions:
        login_sessions = [sid for sid in login_sessions if await session_cache.get(sid) is not None]
        login_sessions.append(session_id)
        await session_cache.set(CacheKeyEnum.SESSION_IDS, login_sessions, 0)
    response.set_cookie(CommonConst.SESSION_ID, session_id, TimeConst.COOKIE_MAX_AGE, domain=env.BASE_DOMAIN, secure=True, httponly=True, samesite='strict')
    response.set_cookie(CommonConst.COOKIE_SIGN, hmac_sign(session_id), TimeConst.COOKIE_MAX_AGE, domain=env.BASE_DOMAIN, secure=True, httponly=True, samesite='strict')


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
    response.delete_cookie(CommonConst.SESSION_ID, domain=env.BASE_DOMAIN)
    response.delete_cookie(CommonConst.COOKIE_SIGN, domain=env.BASE_DOMAIN)
    await session_cache.delete(session_id)
