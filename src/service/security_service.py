import asyncio
import jwt
from datetime import datetime, timedelta
from typing import cast, Coroutine

import bcrypt
from fastapi import Depends, Header, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from redis.asyncio import Redis

from config import Config, logger
from dao import AsyncRedis
from schemas import UserOutput


oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl='auth', auto_error=False
)


async def optional_login_required(
    response: Response,
    access_token: str = Depends(oauth2_scheme_optional),
    refresh_token: str | None = Header(default=None)
) -> UserOutput | None:
    if access_token is None:
        return None
    try:
        data = jwt.decode(
            jwt=access_token,
            key=Config.jwt.key,
            algorithms=[Config.jwt.algorithm]
        )
    except jwt.ExpiredSignatureError:
        data = jwt.decode(
            jwt=refresh_token,
            key=Config.jwt.key,
            algorithms=[Config.jwt.algorithm]
        )
        response.headers['X-token-need-refresh'] = 'true'
    except Exception as e:
        logger.warn(e)
        return None
    return UserOutput(**data)


async def login_required(
    result: UserOutput = Depends(optional_login_required)
) -> UserOutput:
    if result is None:
        raise HTTPException(status_code=401, detail='unauthenticated')
    return result


async def login_throttle(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    redis: Redis = Depends(AsyncRedis.get_connection)
):
    res = await asyncio.gather(
        redis.get(f'login_failure:ip:{request.client.host}'),
        redis.get(f'login_failure:username:{form_data.username}')
    )
    # NOTICE: everything except 0, False, None make any() True
    if any(res):
        logger.info(
            f"""failed to login for {form_data.username},
            from {request.client.host}""",
        )
        raise HTTPException(
            status_code=403,
            detail=f"""too frequent attempt,
            username: {form_data.username}
            address: {request.client.host}"""
        )
    try:
        yield  # login here
    except Exception as e:
        logger.info('failed to login', e)
        await asyncio.gather(
            cast(Coroutine, redis.set(
                f'login_failure:ip:{request.client.host}',
                'True', ex=30
            )),
            cast(Coroutine, redis.set(
                f'login_failure:username:{form_data.username}',
                'True', ex=30
            ))
        )
        raise HTTPException(status_code=401, detail='failed to login')


class SecurityService:
    optional_login_required: callable = optional_login_required
    login_required: callable = login_required
    login_throttle: callable = login_throttle

    @staticmethod
    def generate_salt() -> str:
        return bcrypt.gensalt().decode()

    @staticmethod
    def get_password_hash(plain_password: str, salt: str) -> str:
        return bcrypt.hashpw(
            plain_password.encode(), salt.encode()
        ).decode()

    @classmethod
    def verify_password(
        cls,
        plain_password: str,
        salt: str,
        password_hash: str
    ) -> bool:
        _ = salt
        return bcrypt.checkpw(plain_password.encode(), password_hash.encode())

    @staticmethod
    def create_jwt_token(
        user_info: UserOutput,
        timeout_hour: int | None = 1  # default for access_token
    ) -> bytes:
        data = user_info.dict()
        delta = timedelta(hours=timeout_hour)
        data.update({'exp': datetime.utcnow() + delta})
        return jwt.encode(payload=data, **Config.jwt.__dict__)


class RoleRequired:
    def __init__(self, required_role: str):
        self.required_role = required_role

    async def __call__(
        self,
        user_output: UserOutput = Depends(SecurityService.login_required)
    ) -> UserOutput:

        for role in user_output.roles:
            if role.name == 'admin' or self.required_role == role.name:
                return user_output

        raise HTTPException(status_code=403, detail='no permission')
