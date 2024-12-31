import base64
import json
import os
from logging import CRITICAL

import httpx
from httpx import Response
from loguru import logger as log

from wwricu.domain.common import CommonConstant, ConfigCenterConst, GithubContentResponse, retry


class ConfigClass(object):
    @classmethod
    def init(cls, **kwargs):
        for k, v in kwargs.items():
            if k in cls.__annotations__:
                setattr(cls, k, v)


class StorageConfig(ConfigClass):
    region: str
    s3: str = 's3'
    access_key: str
    secret_key: str
    bucket: str


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


@retry()
def download_config():
    try:
        with open(CommonConstant.TOKEN_PATH) as f:
            token = f.readline()
    except (Exception,):
        token = os.environ.get(ConfigCenterConst.TOKEN_KEY)
    if not token:
        log.info('Config center disabled')
        return
    response: Response = httpx.get(ConfigCenterConst.URL, headers=dict(
        Accept=ConfigCenterConst.ACCEPT,
        Authorization=ConfigCenterConst.AUTHORIZATION.format(token=token.strip())
    ))
    github_response = GithubContentResponse.model_validate(response.json())
    content: bytes = base64.b64decode(github_response.content.encode())
    with open(CommonConstant.CONFIG_PATH, 'wb+') as f:
        f.write(content)
        log.info(f'Download {ConfigCenterConst.URL} to {CommonConstant.CONFIG_PATH}')


def init():
    if __debug__:
        log.warning('APP RUNNING ON DEBUG MODE')
    try:
        download_config()
    except Exception as e:
        log.warning(f'Failed to download config: {e}')
    with open(CommonConstant.CONFIG_PATH) as conf:
        Config.load(**json.load(conf))
        log.info('Config init')
