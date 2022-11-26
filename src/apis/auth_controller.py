from fastapi import Depends, APIRouter, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from service import SecurityService, UserService
from schemas import UserInput, UserOutput, TokenResponse
from core.dependency import requires_login, get_db


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("", response_model=UserOutput)
async def get_current_user(user_output: UserOutput = Depends(requires_login)):
    return user_output


@auth_router.post("", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db)):
    user_output = UserService \
        .user_login(UserInput(username=form_data.username,
                              password=form_data.password),
                    db)
    access_token = SecurityService.create_jwt_token(user_output)
    refresh_token = SecurityService.create_jwt_token(user_output, True)
    return TokenResponse(access_token=access_token,
                         refresh_token=refresh_token)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(response: Response,
                  cur_user: UserOutput = Depends(requires_login)):
    access_token = SecurityService.create_jwt_token(cur_user)
    refresh_token = SecurityService.create_jwt_token(cur_user, True)
    response.headers['X-token-need-refresh'] = 'false'
    return TokenResponse(access_token=access_token,
                         refresh_token=refresh_token)
