import json
import sys
from logging import CRITICAL


class ConfigClass(object):
    @classmethod
    def init(cls, **kwargs):
        for k, v in kwargs.items():
            if k in cls.__annotations__:
                setattr(cls, k, v)


class StorageConfig(ConfigClass):
    bucket: str
    domain: str
    security_key: str
    access_key: str
    timeout: int = 3600


class DatabaseConfig(ConfigClass):
    engine: str
    username: str
    password: str
    host: str
    port: int
    database: str
    url: str

    @classmethod
    def get_url(cls):
        try:
            return cls.url
        except (Exception,):
            return f'{cls.engine}://{cls.username}:{cls.password}@{cls.host}:{cls.port}/{cls.database}'


class AdminConfig(ConfigClass):
    username: str
    password: str
    secure_key: str
    secure_key_bytes: bytes


class Config(ConfigClass):
    app: str = 'main:app'
    host: str = '0.0.0.0'
    port: int = 8000
    log_level: int = CRITICAL
    encoding: str = 'utf-8'

    @classmethod
    def load(cls, admin_config: dict, database_config: dict, storage_config: dict, **kwargs):
        cls.init(**kwargs)
        AdminConfig.init(**admin_config)
        DatabaseConfig.init(**database_config)
        StorageConfig.init(**storage_config)


def init(path: str = 'conf/config.json'):
    sys.tracebacklimit = 0
    with open(path) as f:
        text = json.load(f)
    Config.load(**text)
