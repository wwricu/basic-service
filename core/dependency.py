import jwt

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from schemas import UserOutput
from core.config import Config


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def login_user(token: str = Depends(oauth2_scheme)):
    data = jwt.decode(token,
                      key=Config.jwt_secret,
                      algorithms=['HS256'])

    # if data['exp'] > datetime.utcnow():
    #     raise Exception('token expire')

    return UserOutput(id=data['id'],
                      username=data['username'],
                      email=data['email'],
                      roles=data['roles'])


def requires_roles(role: str,
                   user_output: UserOutput = Depends(login_user)):
    print(role)
    for r in user_output.roles:
        if r == role:
            return user_output

    raise Exception('no permission!')
