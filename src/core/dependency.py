import jwt

from fastapi import Depends, HTTPException, Header, Response
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from schemas import UserOutput
from core.config import Config
from service import DatabaseService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


async def requires_login(response: Response,
                         access_token: str = Depends(oauth2_scheme),
                         refresh_token: Optional[str] = Header(default=None))\
        -> (UserOutput, bool):
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
        except Exception as e:
            print(e)
            raise HTTPException(status_code=403, detail="token expired")

    return UserOutput(id=data['id'],
                      username=data['username'],
                      email=data['email'],
                      roles=data['roles'])


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
