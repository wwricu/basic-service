import jwt

from fastapi import Depends, APIRouter, Response, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from dao import AsyncDatabase
from service import SecurityService, UserService
from schemas import UserInput, UserOutput, TokenResponse
from config import Config


auth_router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)


async def optional_login_required(
        response: Response,
        access_token: str = Depends(oauth2_scheme_optional),
        refresh_token: str | None = Header(default=None)
) -> UserOutput | None:
    if access_token is None:
        return None
    try:
        data = jwt.decode(access_token,
                          key=Config.jwt_secret,
                          algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        try:
            data = jwt.decode(refresh_token,
                              key=Config.jwt_secret,
                              algorithms=['HS256'])
            response.headers['X-token-need-refresh'] = 'true'
        except jwt.ExpiredSignatureError:
            print('token expired')
            return None
    except Exception as e:
        print(e)
        return None

    return UserOutput(id=data['id'],
                      username=data['username'],
                      email=data['email'],
                      roles=data['roles'])


async def requires_login(
        result: UserOutput = Depends(optional_login_required)
) -> UserOutput:

    if result is None:
        raise HTTPException(status_code=401, detail="unauthenticated")
    return result


class RequiresRoles:
    def __init__(self, required_role: str):
        self.required_role = required_role

    def __call__(
            self, user_output: UserOutput = Depends(requires_login)
    ) -> UserOutput:

        for role in user_output.roles:
            if role.name == 'admin' or self.required_role == role:
                return user_output

        raise HTTPException(status_code=403, detail="no permission")


@auth_router.get("", response_model=UserOutput)
async def get_current_user(user_output: UserOutput = Depends(requires_login)):
    return user_output


@auth_router.post("",
                  dependencies=[Depends(AsyncDatabase.open_session)],
                  response_model=TokenResponse)
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
                  cur_user: UserOutput = Depends(requires_login)):
    access_token = SecurityService.create_jwt_token(cur_user)
    refresh_token = SecurityService.create_jwt_token(cur_user, True)
    response.headers['X-token-need-refresh'] = 'false'
    return TokenResponse(access_token=access_token,
                         refresh_token=refresh_token)
