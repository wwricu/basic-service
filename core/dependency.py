import jwt

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from schemas import UserOutput
from core.config import Config


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def requires_login(token: str = Depends(oauth2_scheme)):
    data = jwt.decode(token,
                      key=Config.jwt_secret,
                      algorithms=['HS256'])

    # if data['exp'] > datetime.utcnow():
    #     raise Exception('token expire')

    return UserOutput(id=data['id'],
                      username=data['username'],
                      email=data['email'],
                      roles=data['roles'])


class RequiresRoles:
    def __init__(self, required_role: str):
        self.required_role = required_role

    def __call__(self,
                 user: UserOutput = Depends(requires_login)) -> UserOutput:

        for role in user.roles:
            if role == 'admin' or self.required_role == role:
                return user

        raise HTTPException(status_code=403, detail="no permission")
