import secrets
import hashlib
import jwt

from datetime import datetime, timedelta

from schemas import UserInfo


class SecurityService:
    __jwt_headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    __jwt_salt = "1155e364ad1e604c968bb25b0fcb9ea79b509facb4e9fc5a6f7b01905e6f963f"

    @staticmethod
    def generate_salt():
        return secrets.token_urlsafe()

    @staticmethod
    def get_password_hash(plain_password, salt):
        after_salt = hashlib.md5(plain_password.encode(encoding='utf-8'))\
                                               .hexdigest() + salt
        return hashlib.md5(after_salt.encode(encoding='utf-8')).hexdigest()

    @staticmethod
    def verify_password(plain_password, salt, password_hash):
        after_salt = hashlib.md5(plain_password.encode(encoding='utf-8')) \
                                               .hexdigest() + salt
        return password_hash == hashlib.md5(after_salt.encode(encoding='utf-8'))\
                                       .hexdigest()

    @classmethod
    def create_access_token(cls, user_info: UserInfo):
        data = user_info.dict()

        data.update({"exp": datetime.utcnow() + timedelta(minutes=60)})
        return jwt.encode(payload=data,
                          key=cls.__jwt_salt,
                          algorithm='HS256',
                          headers=cls.__jwt_headers)

    @classmethod
    def verify_token(cls, token: str):
        data = jwt.decode(token,
                          cls.__jwt_salt,
                          algorithms=['HS256'])

        if data['exp'] > datetime.utcnow():
            raise Exception('token expire')

        return UserInfo(id=data['id'],
                        username=data['username'],
                        email=data['email'],
                        roles=data['roles'])
