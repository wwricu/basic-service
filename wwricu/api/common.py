from fastapi import APIRouter, Depends, Request, Response, status, HTTPException
from fastapi.responses import RedirectResponse
from loguru import logger as log

from wwricu.domain.common import LoginRO, LoginVO
from wwricu.domain.enum import PostStatusEnum
from wwricu.service import common_service, post_service, security_service

common_api = APIRouter(prefix='/admin', tags=['Common API'])
image_api = APIRouter(tags=['Image API'])


@common_api.post('/login', response_model=LoginVO)
async def login_api(login_request: LoginRO, request: Request, response: Response):
    return await security_service.authenticate(login_request, request, response)


@common_api.get('/logout', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def logout_api(request: Request, response: Response):
    await security_service.logout(request, response)


@common_api.get('/info', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def info_api():
    return


@image_api.get('/image/post/{post_id}/{key}')
async def post_image_api(post_id: int, key: str, is_admin: bool = Depends(security_service.is_admin)):
    if not is_admin and await post_service.get_status(post_id) != PostStatusEnum.PUBLISHED:
        log.warning(f'{post_id=} {key=}')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return RedirectResponse(
        url=await common_service.get_image_url(f'post/{post_id}/{key}'),
        status_code=status.HTTP_302_FOUND,
        headers={'Cache-Control': 'public, max-age=1800, s-maxage=1200, must-revalidate'},
    )
