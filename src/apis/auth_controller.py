from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from service import SecurityService, UserService
from schemas import UserInput, UserOutput
from core.dependency import requires_login, get_db


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.get("", response_model=UserOutput)
async def get_current_user(auth_result: (UserOutput, bool) = Depends(requires_login)):
    return auth_result[0]


@auth_router.post("")
async def login(form_data: OAuth2PasswordRequestForm = Depends(),
                db: Session = Depends(get_db)):
    user_output = UserService \
        .user_login(UserInput(username=form_data.username,
                              password=form_data.password),
                    db)
    jwt = SecurityService.create_access_token(user_output)
    return {"access_token": jwt, "refresh_token": jwt, "token_type": "bearer"}
