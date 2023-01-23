import hashlib
import jwt
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException, Response
from fastapi.security import OAuth2PasswordBearer

from config import Config, logger
from schemas import UserOutput


class SecurityService:
    __oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth",
                                                    auto_error=False)

    # TODO: async dependency
    @staticmethod
    def optional_login_required(
            response: Response,
            access_token: str = Depends(__oauth2_scheme_optional),
            refresh_token: str | None = Header(default=None)
    ) -> UserOutput | None:
        if access_token is None:
            return None
        try:
            data = jwt.decode(access_token,
                              key=Config.jwt.key,
                              algorithms=[Config.jwt.algorithm])
        except jwt.ExpiredSignatureError:
            try:
                data = jwt.decode(refresh_token,
                                  key=Config.jwt.key,
                                  algorithms=[Config.jwt.algorithm])
                response.headers['X-token-need-refresh'] = 'true'
            except jwt.ExpiredSignatureError:
                logger.info('token expired')
                return None
        except Exception as e:
            logger.warn(e)
            return None

        return UserOutput(id=data['id'],
                          username=data['username'],
                          email=data['email'],
                          roles=data['roles'])

    @staticmethod
    def requires_login(
            result: UserOutput = Depends(optional_login_required)
    ) -> UserOutput:

        if result is None:
            raise HTTPException(status_code=401, detail="unauthenticated")
        return result

    @staticmethod
    def generate_salt() -> str:
        return secrets.token_hex()

    @staticmethod
    def get_password_hash(plain_password: str, salt: str) -> str:
        after_salt = hashlib.sha256(
            plain_password.encode(encoding='utf-8')
        ).hexdigest() + salt
        return hashlib.sha256(
            after_salt.encode(encoding='utf-8')
        ).hexdigest()

    @classmethod
    def verify_password(cls,
                        plain_password: str,
                        salt: str,
                        password_hash: str) -> bool:
        return password_hash == cls.get_password_hash(plain_password, salt)

    @staticmethod
    def create_jwt_token(user_info: UserOutput,
                         refresh: bool | None = False) -> bytes:
        data = user_info.dict()
        delta = timedelta(minutes=60)
        if refresh:
            delta = timedelta(days=7)

        data.update({"exp": datetime.utcnow() + delta})
        return jwt.encode(payload=data, **Config.jwt.__dict__)


class RequiresRoles:
    def __init__(self, required_role: str):
        self.required_role = required_role

    def __call__(
            self,
            user_output: UserOutput = Depends(SecurityService.requires_login)
    ) -> UserOutput:

        for role in user_output.roles:
            if role.name == 'admin' or self.required_role == role:
                return user_output

        raise HTTPException(status_code=403, detail="no permission")
