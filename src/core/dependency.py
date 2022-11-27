import jwt

from fastapi import Depends, HTTPException, Header, Response
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from schemas import UserOutput
from core.config import Config
from service import DatabaseService


oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)


async def optional_login_required(response: Response,
                                  access_token: str = Depends(oauth2_scheme_optional),
                                  refresh_token: Optional[str] = Header(default=None))\
        -> Optional[UserOutput]:
    if access_token is None or refresh_token is None:
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
            raise HTTPException(status_code=403, detail="token expired")

    return UserOutput(id=data['id'],
                      username=data['username'],
                      email=data['email'],
                      roles=data['roles'])


async def requires_login(result:
                         UserOutput = Depends(optional_login_required)) -> UserOutput:
    if result is None:
        raise HTTPException(status_code=401, detail="unauthenticated")

    return result


class RequiresRoles:
    def __init__(self, required_role: str):
        self.required_role = required_role

    def __call__(self,
                 user_output: UserOutput = Depends(requires_login))\
            -> UserOutput:

        for role in user_output.roles:
            if role.name == 'admin' or self.required_role == role:
                return user_output

        raise HTTPException(status_code=403, detail="no permission")


def get_db():
    db = DatabaseService.get_session()
    try:
        yield db
    finally:
        db.close()
