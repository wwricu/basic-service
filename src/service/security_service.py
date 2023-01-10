import secrets
import hashlib
import jwt

from datetime import datetime, timedelta
from config import Config
from schemas import UserOutput


class SecurityService:
    @staticmethod
    def generate_salt() -> str:
        return secrets.token_urlsafe()

    @staticmethod
    def get_password_hash(plain_password, salt) -> str:
        after_salt = hashlib.md5(
            plain_password.encode(encoding='utf-8')
        ).hexdigest() + salt
        return hashlib.md5(after_salt.encode(encoding='utf-8')).hexdigest()

    @staticmethod
    def verify_password(plain_password, salt, password_hash) -> str:
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
        return jwt.encode(payload=data,
                          key=Config.jwt_secret,
                          algorithm='HS256',
                          headers={
                              "alg": "HS256",
                              "typ": "JWT"
                          })

    @staticmethod
    def verify_token(token: str) -> UserOutput:
        data = jwt.decode(token,
                          key=Config.jwt_secret,
                          algorithms=['HS256'])

        return UserOutput(id=data['id'],
                          username=data['username'],
                          email=data['email'],
                          roles=data['roles'])
