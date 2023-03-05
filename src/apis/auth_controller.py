from fastapi import APIRouter, Depends, Header, Response
from fastapi.security import OAuth2PasswordRequestForm

from dao import AsyncDatabase
from service import APIThrottle, SecurityService
from schemas import TokenResponse, UserOutput


auth_router = APIRouter(prefix='/auth', tags=['auth'])
ACCESS_TIMEOUT_HOUR, REFRESH_TIMEOUT_HOUR = 1, 24 * 7


@auth_router.get('', response_model=UserOutput)
async def get_current_user(
    user_output: UserOutput = Depends(SecurityService.optional_login_required)
):
    return user_output


@auth_router.post(
    '', response_model=TokenResponse,
    dependencies=[
        Depends(AsyncDatabase.open_session),
        Depends(APIThrottle(30))
    ]
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    two_fa_code: str | None = Header(default=None)
):
    user_output = await SecurityService.user_login_2fa(
        form_data.username,
        form_data.password.encode(),
        two_fa_code
    )

    access_token = SecurityService.create_jwt_token(user_output)
    refresh_token = SecurityService.create_jwt_token(
        user_output, REFRESH_TIMEOUT_HOUR
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
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
        access_token=access_token,
        refresh_token=refresh_token
    )
