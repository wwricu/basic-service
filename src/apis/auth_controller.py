from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from service import SecurityService, UserService
from schemas import UserInput, UserOutput
from core.dependency import requires_login


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("", response_model=UserOutput)
async def get_current_user(user_output: UserOutput = Depends(requires_login)):
    return user_output


@auth_router.post("")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_output = UserService \
        .user_login(UserInput(username=form_data.username,
                              password=form_data.password))
    jwt = SecurityService.create_access_token(user_output)
    return {"access_token": jwt, "token_type": "bearer"}
