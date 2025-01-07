import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from wwricu.domain.common import CommonConstant, HttpErrorDetail
from wwricu.domain.input import LoginRO
from wwricu.service.cache import cache_delete, cache_set
from wwricu.service.common import admin_only, hmac_sign, validate_cookie, admin_login


common_api = APIRouter(tags=['Common API'])


@common_api.post('/login')
async def login(login_request: LoginRO, response: Response):
    if admin_login(login_request.username, login_request.password) is not True:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)
    session_id = uuid.uuid4().hex
    cookie_sign = hmac_sign(session_id)
    await cache_set(session_id, CommonConstant.COOKIE_TIMEOUT_SECOND)
    response.set_cookie(CommonConstant.SESSION_ID, session_id, secure=True, httponly=True, samesite='lax')
    response.set_cookie(CommonConstant.COOKIE_SIGN, cookie_sign, secure=True, httponly=True, samesite='lax')


@common_api.get('/logout', dependencies=[Depends(admin_only)])
async def logout(request: Request, response: Response):
    if (session_id := request.cookies.get(CommonConstant.SESSION_ID)) is None:
        return
    await cache_delete(session_id)
    response.delete_cookie(CommonConstant.SESSION_ID)


@common_api.get('/info', response_model=bool)
async def info(request: Request) -> bool:
    session_id = request.cookies.get(CommonConstant.SESSION_ID)
    cookie_sign = request.cookies.get(CommonConstant.COOKIE_SIGN)
    if valid := await validate_cookie(session_id, cookie_sign):
        await cache_set(session_id, CommonConstant.COOKIE_TIMEOUT_SECOND)
    return valid
