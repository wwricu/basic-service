import asyncio
import jwt
import secrets
from datetime import datetime, timedelta
from typing import cast, Coroutine

import bcrypt
from fastapi import Depends, Header, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis

from .mail_service import MailService
from config import Config, logger, Status
from dao import AsyncRedis, BaseDao
from models import SysUser
from schemas import UserInput, UserOutput


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='unauthenticated'
        )
    return result


class SecurityService:
    optional_login_required: callable = optional_login_required
    login_required: callable = login_required

    @staticmethod
    def get_password_hash(plain_password: bytes) -> bytes | None:
        if plain_password is None:
            return None
        return bcrypt.hashpw(plain_password, bcrypt.gensalt())

    @classmethod
    def verify_password(
        cls,
        plain_password: bytes,
        password_hash: bytes
    ) -> bool:
        return bcrypt.checkpw(plain_password, password_hash)

    @staticmethod
    def create_jwt_token(
        user_info: UserOutput,
        timeout_hour: int | None = 1  # default for access_token
    ) -> bytes:
        data = user_info.dict()
        delta = timedelta(hours=timeout_hour)
        data.update({'exp': datetime.utcnow() + delta})
        return jwt.encode(payload=data, **Config.jwt.__dict__)

    @classmethod
    async def user_login_2fa(
        cls,
        username: str,
        password: bytes,
        two_fa_code: str | None = None
    ):
        redis = await AsyncRedis.get_connection()
        sys_user, need_2fa, existed_code = await asyncio.gather(
            BaseDao.select(UserInput(username=username), SysUser),
            redis.get(f'login_failure:username:{username}'),
            redis.get(f'2fa_code:username:{username}'),
        )
        sys_user = sys_user[0]

        if cls.verify_password(password, sys_user.password_hash) is False:
            await cast(Coroutine, redis.set(
                f'login_failure:username:{username}', 'True'
            ))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='password mismatch'
            )
        '''
        1. First login success, nothing happens
        2. Login failed, set need_2fa
        3. Login success, after a failure (need_2fa set)
            if no 2fa code then generate and send it
            else raise exception
        4. IP throttle controlled by another dependency
        '''
        if need_2fa is None:
            return UserOutput.init(sys_user)
        # 2fa enforced below
        if not isinstance(existed_code, bytes):
            # no 2fa code, generate 6 digits and return
            two_fa_code = str(secrets.randbelow(1000000)).zfill(6)
            asyncio.create_task(MailService.send_mail(
                [sys_user.email],
                subject=f'verification code for {username}',
                message=two_fa_code
            ))
            asyncio.create_task(cast(Coroutine, redis.set(
                f'2fa_code:username:{username}',
                two_fa_code, ex=600  # 10min
            )))
            raise HTTPException(
                status_code=Status.HTTP_440_2FA_NEEDED,
                detail='2FA enforced'
            )
        if existed_code.decode() != two_fa_code:
            # failed 2fa
            raise HTTPException(
                status_code=Status.HTTP_441_2FA_FAILED,
                detail='failed 2fa'
            )
        # success
        asyncio.create_task(cast(Coroutine, redis.delete(
            f'login_failure:username:{username}'
        )))
        asyncio.create_task(cast(Coroutine, redis.delete(
            f'2fa_code:username:{username}'
        )))
        return UserOutput.init(sys_user)


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

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='no permission'
        )


class APIThrottle:
    def __init__(self, throttle: int | None = 30):
        self.throttle = throttle

    async def __call__(
        self,
        request: Request,
        redis: Redis = Depends(AsyncRedis.get_connection)
    ):
        key = f'login_failure:url:{request.url}:ip:{request.client.host}'
        if await redis.get(key) is not None:
            message = 'too frequent access to {url} from {host}'.format(
                url=request.url,
                host=request.client.host
            )
            # HTTP 429 Too Many Requests
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message
            )
        asyncio.create_task(cast(
            Coroutine, redis.set(key, '0', ex=self.throttle)
        ))
