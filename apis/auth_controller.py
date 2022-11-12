from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from service import SecurityService, UserService
from schemas import Response, UserInput, UserOutput
from core.dependency import requires_login


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
auth_router = APIRouter(prefix="/auth")


@auth_router.get("/user_info", response_model=UserOutput)
async def get_current_user(user_output: UserOutput = Depends(requires_login)):
    return user_output


@auth_router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user_output = UserService \
            .user_login(UserInput(username=form_data.username,
                                  password=form_data.password))
        jwt = SecurityService.create_access_token(user_output)
        return {"access_token": jwt, "token_type": "bearer"}
    except Exception as e:
        return Response(status='failure',
                        message=e.__str__())
