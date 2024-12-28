from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import HTTPException, status

from wwricu.domain.common import HttpErrorDetail


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
