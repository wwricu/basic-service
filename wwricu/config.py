import json
from logging import CRITICAL

import requests
from loguru import logger as log

from wwricu.domain.common import GithubContentResponse, CommonConstant


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


class ConfigCenter(ConfigClass):
    url: str
    headers: dict[str, str]


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


def download_config():
    with open(CommonConstant.CONFIG_CENTER_PATH) as f:
        json_data = json.load(f)
    ConfigCenter.init(**json_data)
    response = requests.get(ConfigCenter.url, headers=ConfigCenter.headers)
    content_response = GithubContentResponse.model_validate(response.json())
    response = requests.get(content_response.download_url)
    with open(CommonConstant.CONFIG_PATH, 'wb+') as f:
        f.write(response.content)
    log.info(f'Download {ConfigCenter.url} to {CommonConstant.CONFIG_PATH}')


if not __debug__:
    download_config()
with open(CommonConstant.CONFIG_PATH) as conf:
    Config.load(**json.load(conf))
