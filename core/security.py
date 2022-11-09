import secrets
import hashlib

from jwt import JWT
from datetime import datetime, timedelta
from passlib.context import CryptContext

from core import Config
from schemas import UserInfo


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_salt():
    return secrets.token_urlsafe()


def get_password_hash(plain_password, salt):
    after_salt = hashlib.md5(plain_password.encode(encoding='utf-8'))\
                                           .hexdigest() + salt
    return hashlib.md5(after_salt.encode(encoding='utf-8')).hexdigest()


def verify_password(plain_password, salt, password_hash):
    after_salt = hashlib.md5(plain_password.encode(encoding='utf-8')) \
                                           .hexdigest() + salt
    return password_hash == hashlib.md5(after_salt.encode(encoding='utf-8'))\
                                   .hexdigest()


def create_access_token(user_info: UserInfo):
    data = user_info.dict()

    data.update({"exp": datetime.utcnow() + timedelta(minutes=60)})
    return JWT().encode(data, Config.jwt_secret)
