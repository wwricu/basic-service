import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from wwricu.config import AdminConfig

from wwricu.domain.common import CommonConstant, HttpErrorDetail
from wwricu.domain.enum import DatabaseActionEnum
from wwricu.domain.input import LoginRO
from wwricu.service.cache import cache
from wwricu.service.common import admin_only, hmac_sign, validate_cookie, admin_login
from wwricu.service.database import database_restore, database_backup


common_api = APIRouter(tags=['Common API'])


@common_api.post('/login')
async def login(login_request: LoginRO, response: Response):
    if await admin_login(login_request.username, login_request.password) is not True:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)
    if (session_id := await cache.get(login_request.username)) is None:
        session_id = uuid.uuid4().hex
        await cache.set(login_request.username, session_id, CommonConstant.COOKIE_TIMEOUT_SECOND)
    cookie_sign = hmac_sign(session_id)
    await cache.set(session_id, int(time.time()), CommonConstant.COOKIE_TIMEOUT_SECOND)
    response.set_cookie(CommonConstant.SESSION_ID, session_id, secure=True, httponly=True, samesite='lax')
    response.set_cookie(CommonConstant.COOKIE_SIGN, cookie_sign, secure=True, httponly=True, samesite='lax')


@common_api.get('/logout', dependencies=[Depends(admin_only)])
async def logout(request: Request, response: Response):
    if (session_id := request.cookies.get(CommonConstant.SESSION_ID)) is None:
        return
    await cache.delete(session_id)
    await cache.delete(AdminConfig.username)
    response.delete_cookie(CommonConstant.SESSION_ID)
    response.delete_cookie(CommonConstant.COOKIE_SIGN)


@common_api.get('/info', response_model=bool)
async def info(request: Request) -> bool:
    session_id = request.cookies.get(CommonConstant.SESSION_ID)
    cookie_sign = request.cookies.get(CommonConstant.COOKIE_SIGN)
    if valid := await validate_cookie(session_id, cookie_sign):
        await cache.set(session_id, int(time.time()), CommonConstant.COOKIE_TIMEOUT_SECOND)
    return valid


@common_api.get('/database', dependencies=[Depends(admin_only)])
async def database(action: DatabaseActionEnum | None = DatabaseActionEnum.RESTORE):
    if action == DatabaseActionEnum.RESTORE:
        await database_restore()
    elif action == DatabaseActionEnum.BACKUP:
        database_backup()
