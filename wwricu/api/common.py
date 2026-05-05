from fastapi import APIRouter, Depends, Request, Response

from wwricu.domain.common import LoginRO, LoginVO
from wwricu.service import security_service

common_api = APIRouter(tags=['Common API'])


@common_api.post('/login', dependencies=[Depends(security_service.login_limiter)], response_model=LoginVO)
async def login_api(login_request: LoginRO, request: Request, response: Response):
    return await security_service.authenticate(login_request, request, response)


@common_api.get('/logout', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def logout_api(request: Request, response: Response):
    await security_service.logout(request, response)


@common_api.get('/info', dependencies=[Depends(security_service.require_admin)], response_model=None)
async def info_api():
    return
