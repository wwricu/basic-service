import jwt
from fastapi import HTTPException

from service import Config
from schemas import UserInfo


def get_user(token: str):
    try:
        data = jwt.decode(token, Config.jwt_secret, algorithms='HS256')
        username = data.get('username', -1)
    except Exception as e:
        raise HTTPException(status_code=403, detail='access denied')

    if username == '-1':
        raise HTTPException(status_code=400, detail='user access denied')

    return UserInfo(id=data['id'],
                    username=data['username'],
                    email=data['email'],
                    roles=data['roles'])
