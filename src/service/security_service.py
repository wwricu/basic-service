import secrets
import hashlib
import jwt

from fastapi import Depends, Response, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from config import Config
from schemas import UserOutput


class SecurityService:
    __oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth",
                                                    auto_error=False)

    @staticmethod
    async def optional_login_required(
            response: Response,
            access_token: str = Depends(__oauth2_scheme_optional),
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

    @staticmethod
    async def requires_login(
            result: UserOutput = Depends(optional_login_required)
    ) -> UserOutput:

        if result is None:
            raise HTTPException(status_code=401, detail="unauthenticated")
        return result

    @staticmethod
    def generate_salt() -> str:
        return secrets.token_urlsafe()

    @staticmethod
    def get_password_hash(plain_password: str, salt: str) -> str:
        after_salt = hashlib.md5(
            plain_password.encode(encoding='utf-8')
        ).hexdigest() + salt
        return hashlib.md5(after_salt.encode(encoding='utf-8')).hexdigest()

    @staticmethod
    def verify_password(plain_password: str,
                        salt: str,
                        password_hash: str) -> bool:
        after_salt = hashlib.md5(
            plain_password.encode(encoding='utf-8')
        ).hexdigest() + salt
        return password_hash == hashlib.md5(
            after_salt.encode(encoding='utf-8')
        ).hexdigest()

    @staticmethod
    def create_jwt_token(user_info: UserOutput,
                         refresh: bool | None = False) -> bytes:
        data = user_info.dict()
        delta = timedelta(minutes=60)
        if refresh:
            delta = timedelta(days=7)

        data.update({"exp": datetime.utcnow() + delta})
        return jwt.encode(payload=data, **Config.jwt.__dict__)

    @staticmethod
    def verify_token(token: str) -> UserOutput:
        data = jwt.decode(token,
                          key=Config.jwt_secret,
                          algorithms=[Config.jwt.algorithm])

        return UserOutput(id=data['id'],
                          username=data['username'],
                          email=data['email'],
                          roles=data['roles'])


class RequiresRoles:
    def __init__(self, required_role: str):
        self.required_role = required_role

    def __call__(
            self, user_output: UserOutput = Depends(SecurityService.requires_login)
    ) -> UserOutput:

        for role in user_output.roles:
            if role.name == 'admin' or self.required_role == role:
                return user_output

        raise HTTPException(status_code=403, detail="no permission")
