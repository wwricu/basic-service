import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from wwricu.domain.common import CommonConstant, HttpErrorDetail
from wwricu.domain.input import LoginRO
from wwricu.service.cache import cache_delete, cache_set
from wwricu.service.common import admin_only, hmac_sign


common_api = APIRouter(tags=['Common API'])


@common_api.post('/login')
async def login(login_request: LoginRO, response: Response):
    if login_request.username != login_request.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)
    session_id = uuid.uuid4().hex
    session_sign = hmac_sign(session_id)
    await cache_set(session_id, int(time.time()))
    response.set_cookie(CommonConstant.SESSION_ID, session_id, secure=True)
    response.set_cookie(CommonConstant.SESSION_SIGN, session_sign, secure=True)


@common_api.get('/logout', dependencies=[Depends(admin_only)])
async def logout(request: Request, response: Response):
    if (session_id := request.cookies.get(CommonConstant.SESSION_ID)) is None:
        return
    cache_delete(session_id)
    response.delete_cookie(CommonConstant.SESSION_ID)
