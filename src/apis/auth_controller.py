from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from config import CustomHeaders, Status
from dao import AsyncDatabase, AsyncRedis, RedisKey
from service import APIThrottle, SecurityService
from schemas import TokenResponse, UserOutput


auth_router = APIRouter(prefix='/auth', tags=['auth'])


@auth_router.get('', response_model=UserOutput)
async def get_current_user(
    user_output: UserOutput = Depends(SecurityService.optional_login_required)
):
    if user_output is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='please login to get user info'
        )
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
    user_output: UserOutput = Depends(SecurityService.verify_2fa_token)
):
    if user_output is not None:
        '''
        Calling login with a 2fa token means 2fa has been triggered
        with a correct password, the need_2fa flag which enforces 2fa
        verification is permanent until a successful 2fa login
        so there is no need to continue password login process
        but directly re-generate and send the verification mail.
        Expiration of 2fa_token is 5min after which user must
        re-input their username and password but they will still
        encounter the permanent need_2fa flag triggered previously.
        Additionally, webpage do not need to intentionally remove
        token because an expired token has no effect to normal login.
        The api was throttled within 30 seconds to limit generation
        as well as possible malicious username-password login attempts.
        '''
        redis = await AsyncRedis.get_connection()
        if await redis.get(
            RedisKey.totp_key(user_output.username)
        ) is not None:
            raise HTTPException(
                status_code=Status.HTTP_441_TOTP_2FA_NEEDED,
                detail='please check your totp application'
            )
        await SecurityService.generate_2fa_code(user_output, redis)
        raise HTTPException(
            status_code=Status.HTTP_440_MAIL_2FA_NEEDED,
            detail='please check the otp sent to {email}'.format(
                email=f'{user_output.email[:2]}****{user_output.email[-2:]}'
            )
        )

    user_output = await SecurityService.user_login(
        form_data.username,
        form_data.password.encode()
    )
    return SecurityService.create_access_tokens(user_output)


@auth_router.post(
    '/2fa', response_model=TokenResponse,
    dependencies=[Depends(APIThrottle(10))]
)
async def login_2fa(
    user_output: UserOutput = Depends(SecurityService.check_2fa_code)
):
    return SecurityService.create_access_tokens(user_output)


@auth_router.post('/refresh', response_model=TokenResponse)
async def refresh(
    response: Response,
    cur_user: UserOutput = Depends(SecurityService.login_required)
):
    response.headers[CustomHeaders.TOKEN_NEED_REFRESH] = 'false'
    return SecurityService.create_access_tokens(cur_user)
