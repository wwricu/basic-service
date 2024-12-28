import base64
import hashlib
import hmac
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import HTTPException, status

from wwricu.domain.common import HttpErrorDetail
from wwricu.config import AdminConfig, Config


admin: ContextVar[bool] = ContextVar('admin', default=False)


async def admin_only():
    if admin.get() is not True:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.NOT_AUTHORIZED)


@asynccontextmanager
async def admin_user():
    admin.set(True)
    try:
        yield
    finally:
        admin.set(False)


def hmac_sign(plain: str):
    return hmac.new(secure_key, plain.encode(Config.encoding), hashlib.sha256).hexdigest()


def hmac_verify(plain: str, sign: str) -> bool:
    if not plain or not sign:
        return False
    return hmac_sign(plain) == sign


secure_key = base64.b64decode(AdminConfig.secure_key.encode(Config.encoding))
