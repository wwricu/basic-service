import base64
import hashlib
import hmac
import time
from contextlib import asynccontextmanager

import bcrypt
from alembic.config import Config
from fastapi import FastAPI, HTTPException, Request, status
from loguru import logger as log

from wwricu.domain.common import HttpErrorDetail, CommonConstant
from wwricu.config import AdminConfig, Config
from wwricu.service.cache import cache
from wwricu.service.category import reset_category_count
from wwricu.service.database import engine
from wwricu.service.tag import reset_tag_count


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await reset_tag_count()
        await reset_category_count()
        log.info(f'listening on {Config.host}:{Config.port}')
        yield
    finally:
        await engine.dispose()
        log.info('THE END')
        await log.complete()


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
