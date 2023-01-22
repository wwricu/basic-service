from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm

from dao import AsyncDatabase
from service import SecurityService, UserService
from schemas import TokenResponse, UserInput, UserOutput


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("", response_model=UserOutput)
async def get_current_user(
        user_output: UserOutput = Depends(SecurityService.optional_login_required)
):
    return user_output


@auth_router.post("", response_model=TokenResponse,
                  dependencies=[Depends(AsyncDatabase.open_session)])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_output = await UserService.user_login(
        UserInput(username=form_data.username, password=form_data.password)
    )
    access_token = SecurityService.create_jwt_token(user_output)
    refresh_token = SecurityService.create_jwt_token(user_output, True)
    return TokenResponse(access_token=access_token,
                         refresh_token=refresh_token)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(response: Response,
                  cur_user: UserOutput = Depends(SecurityService.requires_login)):
    access_token = SecurityService.create_jwt_token(cur_user)
    refresh_token = SecurityService.create_jwt_token(cur_user, True)
    response.headers['X-token-need-refresh'] = 'false'
    return TokenResponse(access_token=access_token,
                         refresh_token=refresh_token)
