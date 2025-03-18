import asyncio
import base64
import hashlib
import hmac
import time
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI, HTTPException, Request, status
from loguru import logger as log
from sqlalchemy import select, func

from wwricu.domain.constant import CommonConstant, HttpErrorDetail
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import CacheKeyEnum, PostStatusEnum, TagTypeEnum
from wwricu.config import AdminConfig, Config
from wwricu.service.cache import cache
from wwricu.service.category import reset_category_count
from wwricu.service.database import engine, get_session, new_session
from wwricu.service.tag import reset_tag_count


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await reset_tag_count()
        await reset_category_count()
        await reset_system_count()
        log.info(f'listening on {Config.host}:{Config.port}')
        yield
    finally:
        await cache.close()
        await engine.dispose()
        log.info('Exit')
        await log.complete()


@asynccontextmanager
async def try_login_lock():
    if await cache.get(CacheKeyEnum.LOGIN_LOCK) is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'LOGIN FORBIDDEN')
    try:
        yield
        await cache.delete(CacheKeyEnum.LOGIN_LOCK)
        await cache.delete(CacheKeyEnum.LOGIN_RETRIES)
    except Exception as e:
        if (retries := await cache.get(CacheKeyEnum.LOGIN_RETRIES)) is None:
            retries = 0
        if retries >= 2:
            await cache.set(CacheKeyEnum.LOGIN_LOCK, True, 600)
            await cache.delete(CacheKeyEnum.LOGIN_RETRIES)
        else:
            await cache.set(CacheKeyEnum.LOGIN_RETRIES, retries + 1, 300)
        raise e


async def reset_system_count():
    post_stmt = select(
        func.count(BlogPost.id)).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    category_stmt = select(
        func.count(PostTag.id)).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_CAT
    )
    tag_stmt = select(
        func.count(PostTag.id)).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG
    )
    async with new_session() as s:
        # single session with transaction cannot be used by gather
        post_count = await s.scalar(post_stmt)
        category_count = await s.scalar(category_stmt)
        tag_count = await s.scalar(tag_stmt)
        await asyncio.gather(
            cache.set(CacheKeyEnum.POST_COUNT, post_count, 0),
            cache.set(CacheKeyEnum.CATEGORY_COUNT, category_count, 0),
            cache.set(CacheKeyEnum.TAG_COUNT, tag_count, 0)
        )


async def update_system_count():
    async with get_session() as s:
        yield
        await s.flush()
        await reset_system_count()


async def admin_login(username: str, password: str) -> bool:
    if __debug__:
        return True
    if username != AdminConfig.username:
        return False
    return bcrypt.checkpw(password.encode(), base64.b64decode(AdminConfig.password))


async def admin_only(request: Request):
    session_id = request.cookies.get(CommonConstant.SESSION_ID)
    cookie_sign = request.cookies.get(CommonConstant.COOKIE_SIGN)
    if await validate_cookie(session_id, cookie_sign) is not True:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.NOT_AUTHORIZED)


def hmac_sign(plain: str):
    return hmac.new(secure_key, plain.encode(Config.encoding), hashlib.sha256).hexdigest()


def hmac_verify(plain: str, sign: str) -> bool:
    if not plain or not sign:
        return False
    return hmac_sign(plain) == sign


async def validate_cookie(session_id: str, cookie_sign: str) -> bool:
    if __debug__ is True:
        return True
    if session_id is None or cookie_sign is None or not isinstance(issue_time := await cache.get(session_id), int):
        return False
    if 0 <= int(time.time()) - issue_time < CommonConstant.EXPIRE_TIME and hmac_verify(session_id, cookie_sign) is True:
        return True
    log.warning(f'Invalid cookie session={session_id} issue_time={issue_time} sign={cookie_sign}')
    return False


secure_key = base64.b64decode(AdminConfig.secure_key.encode(Config.encoding))
