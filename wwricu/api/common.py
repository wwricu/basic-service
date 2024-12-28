import io
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, UploadFile
from loguru import logger as log

from service.common import hmac_sign
from wwricu.domain.common import CommonConstant, HttpErrorDetail
from wwricu.domain.input import LoginRO
from wwricu.domain.output import FileUploadVO
from wwricu.domain.context import admin_only
from wwricu.service.cache import cache_delete, cache_set
from wwricu.service.database import database_session
from wwricu.service.storage import storage_put


api_router = APIRouter(tags=['Common API'], dependencies=[Depends(database_session)])


@api_router.post('/login')
async def login(login_request: LoginRO, response: Response):
    if login_request.username != login_request.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_PASSWORD)
    session_id = uuid.uuid4().hex
    session_sign = hmac_sign(session_id)
    await cache_set(session_id, int(time.time()))
    response.set_cookie(CommonConstant.SESSION_ID, session_id)
    response.set_cookie(CommonConstant.SESSION_SIGN, session_sign)


@api_router.get('/logout', dependencies=[Depends(admin_only)])
async def logout(request: Request, response: Response):
    if (session_id := request.cookies.get(CommonConstant.SESSION_ID)) is None:
        return
    cache_delete(session_id)
    response.delete_cookie(CommonConstant.SESSION_ID)


@api_router.post('/upload', dependencies=[Depends(admin_only)], response_model=FileUploadVO)
async def upload(file: UploadFile, post_id: int | None = None) -> FileUploadVO:
    log.info(f'Upload {file.filename}, size={file.size}kb')
    filename = uuid.uuid4().hex
    if post_id is not None:
        filename = f'{post_id}/{filename}'
    url = await storage_put(filename, io.BytesIO(await file.read()))
    return FileUploadVO(name=filename, location=url)
