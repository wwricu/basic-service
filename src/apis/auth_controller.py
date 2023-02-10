import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from redis import Redis

from dao import AsyncDatabase, AsyncRedis
from service import SecurityService, UserService
from schemas import TokenResponse, UserInput, UserOutput


auth_router = APIRouter(prefix='/auth', tags=['auth'])
ACCESS_TIMEOUT_HOUR, REFRESH_TIMEOUT_HOUR = 1, 24 * 7


@auth_router.get('', response_model=UserOutput)
async def get_current_user(
    user_output: UserOutput = Depends(SecurityService.optional_login_required)
):
    return user_output


@auth_router.post(
    '', response_model=TokenResponse,
    dependencies=[Depends(AsyncDatabase.open_session)]
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    redis: Redis = Depends(AsyncRedis.get_connection)
):
    last_fail_time: bytes = await redis.get(
        f'login_failure:username:{form_data.username}'
    )
    if (
        last_fail_time is not None and
        int(time.time()) - int(last_fail_time.decode()) < 30
    ):
        raise HTTPException(
            status_code=403,
            detail=f'too frequent attempt for {form_data.username}'
        )
    try:
        user_output = await UserService.user_login(
            UserInput(username=form_data.username, password=form_data.password)
        )
    except (Exception,):
        # await here for possable dense requests.
        await redis.set(
            f'login_failure:username:{form_data.username}',
            int(time.time())
        )
        raise HTTPException(status_code=401, detail='password mismatch')

    asyncio.create_task(
        redis.delete(f'login_failure:username:{form_data.username}')
    )
    access_token = SecurityService.create_jwt_token(user_output)
    refresh_token = SecurityService.create_jwt_token(
        user_output, REFRESH_TIMEOUT_HOUR
    )
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token
    )


@auth_router.post('/refresh', response_model=TokenResponse)
async def refresh(
    response: Response,
    cur_user: UserOutput = Depends(SecurityService.login_required)
):
    access_token = SecurityService.create_jwt_token(cur_user)
    refresh_token = SecurityService.create_jwt_token(
        cur_user, REFRESH_TIMEOUT_HOUR
    )
    response.headers['X-token-need-refresh'] = 'false'
    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token
    )
