import base64
import hashlib
import hmac
import time
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import HTTPException, status, FastAPI
from loguru import logger as log

from wwricu.domain.common import HttpErrorDetail, CommonConstant
from wwricu.config import AdminConfig, Config
from wwricu.service.cache import cache_get


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info(f'{CommonConstant.APP_TITLE} {CommonConstant.APP_VERSION} Startup')
    log.info(f'listening on {Config.host}:{Config.port}')
    yield
    log.info('THE END')
    await log.complete()


async def admin_only():
    if admin.get() is not True:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.NOT_AUTHORIZED)


def hmac_sign(plain: str):
    return hmac.new(secure_key, plain.encode(Config.encoding), hashlib.sha256).hexdigest()


def hmac_verify(plain: str, sign: str) -> bool:
    if not plain or not sign:
        return False
    return hmac_sign(plain) == sign


def validate_cookie(session_id: str, cookie_sign: str) -> bool:
    if __debug__ is True:
        return True
    if session_id is None or cookie_sign is None or not isinstance(issue_time := cache_get(session_id), int):
        return False
    if 0 < int(time.time()) - issue_time < CommonConstant.EXPIRE_TIME and hmac_verify(session_id, cookie_sign) is True:
        return True
    return False


admin: ContextVar[bool] = ContextVar('admin', default=False)
secure_key = base64.b64decode(AdminConfig.secure_key.encode(Config.encoding))
