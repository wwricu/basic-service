from jwt import JWT
from datetime import datetime, timedelta
from passlib.context import CryptContext

from core import Config
from schemas import UserInfo


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, password_hash):
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_info: UserInfo):
    data = user_info.dict()

    data.update({"exp": datetime.utcnow() + timedelta(minutes=60)})
    return JWT().encode(data, Config.jwt_secret)
