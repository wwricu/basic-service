import jwt

from fastapi import Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from schemas import UserOutput
from core.config import Config
from service import DatabaseService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


async def requires_login(access_token: str = Depends(oauth2_scheme),
                         refresh_token: Optional[str] = Header(default=None)):
    need_refresh = False
    try:
        data = jwt.decode(access_token,
                          key=Config.jwt_secret,
                          algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        data = jwt.decode(refresh_token,
                          key=Config.jwt_secret,
                          algorithms=['HS256'])
        need_refresh = True

    return UserOutput(id=data['id'],
                      username=data['username'],
                      email=data['email'],
                      roles=data['roles']), need_refresh


class RequiresRoles:
    def __init__(self, required_role: str):
        self.required_role = required_role

    def __call__(self,
                 user: UserOutput = Depends(requires_login)) -> UserOutput:

        for role in user.roles:
            if role.name == 'admin' or self.required_role == role:
                return user

        raise HTTPException(status_code=403, detail="no permission")


def get_db():
    db = DatabaseService.get_session()
    try:
        yield db
    finally:
        db.close()
