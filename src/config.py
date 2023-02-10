import json
import logging
from types import MappingProxyType

from anyio import Path

from models import Folder


logger = logging.getLogger()


class AdminConfig:
    def __init__(
        self,
        username: str,
        password_hash: str,
        salt: str,
        email: str | None = None,
        role: dict | None = MappingProxyType({'name': 'admin'})
    ):
        self.username = username
        self.password_hash = password_hash
        self.salt = salt
        self.email = email
        self.role = role


class DatabaseConfig:
    def __init__(
        self,
        drivername: str,
        username: str,
        password: str,
        host: str | None = '127.0.0.1',
        port: int | None = 3306,
        database: str | None = None
    ):
        self.drivername = drivername
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database = database


class JWTConfig:
    def __init__(
        self,
        key: str,
        algorithm: str | None = 'HS256',
        headers: dict | None = MappingProxyType({
            'alg': 'HS256',
            'typ': 'JWT'
        })
    ):
        self.key = key
        self.algorithm = algorithm
        self.headers = headers


class RedisConfig:
    def __init__(
        self,
        host: str,
        port: int = 6379
    ):
        self.host = host
        self.port = port


class StaticResource:
    def __init__(
        self,
        root_path: str | None = 'static',
        content_path: str | None = 'static/content'
    ):
        self.root_path = root_path
        self.content_path = content_path


class Config:
    database: DatabaseConfig = None
    redis: RedisConfig = None
    admin: AdminConfig = None
    jwt: JWTConfig = None
    static: StaticResource = None
    folders: list[Folder] = []

    @classmethod
    async def init_config(cls, filename: str = 'assets/config.json'):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(levelname)s:     %(message)s'
        ))
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        try:
            config_text = await Path(filename).read_text()
            config_json = json.loads(config_text)
            cls.load_json(**config_json)
            logger.info(f'config file: {filename}')
        except FileNotFoundError:
            logger.info('config file NOT found')

    @classmethod
    def load_json(
        cls,
        database: dict,
        redis: dict,
        admin: dict,
        jwt: dict,
        static: dict,
        folders: dict,
        **kwargs
    ):
        _ = kwargs
        cls.database = DatabaseConfig(**database)
        cls.admin = AdminConfig(**admin)
        cls.jwt = JWTConfig(**jwt)
        cls.redis = RedisConfig(**redis)
        cls.static = StaticResource(**static)
        for folder in folders:
            cls.folders.append(Folder(**folder))
