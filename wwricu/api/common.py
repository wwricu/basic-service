import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from wwricu.domain.common import CommonConstant, HttpErrorDetail, LoginConstant
from wwricu.domain.input import LoginRO
from wwricu.service.cache import cache_delete, cache_set, cache_get
from wwricu.service.common import admin_only, hmac_sign, validate_cookie, admin_login


common_api = APIRouter(tags=['Common API'])


@common_api.post('/login')
async def login(login_request: LoginRO, response: Response):
    if cache_get(LoginConstant.LOCK_KEY) is True:
        return False
    if admin_login(login_request.username, login_request.password) is not True:
        failure_time = await cache_get(LoginConstant.FAILURE_TIME_KEY)
        if failure_time is None:
            failure_time = 0
        failure_time += 1
        if failure_time >= LoginConstant.MAX_TRY:
            await cache_set(LoginConstant.LOCK_KEY, True, LoginConstant.LOCK_TIME)
            await cache_delete(LoginConstant.FAILURE_TIME_KEY)
        else:
            await cache_set(LoginConstant.FAILURE_TIME_KEY, failure_time, LoginConstant.TRY_TIMEOUT)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)

    await cache_delete(LoginConstant.FAILURE_TIME_KEY)
    await cache_delete(LoginConstant.LOCK_KEY)
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
