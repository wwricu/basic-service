import json
from logging import CRITICAL

import boto3
from loguru import logger as log

from wwricu.domain.common import CommonConstant
from wwricu.domain.third import AWSConst, AWSSSMResponse


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
    ssm_client = boto3.client(AWSConst.ssm, region_name=AWSConst.region)
    content = ssm_client.get_parameter(Name=AWSConst.config_key, WithDecryption=False)
    response = AWSSSMResponse.model_validate(content)
    with open(CommonConstant.CONFIG_FILE, 'wt+') as f:
        f.write(response.Parameter.Value)


def init():
    if __debug__:
        log.warning('APP RUNNING ON DEBUG MODE')
    try:
        download_config()
        log.info(f'config downloaded')
    except Exception as e:
        log.warning(f'Failed to download config: {e}, load locally')
    with open(CommonConstant.CONFIG_FILE) as f:
        Config.load(**json.load(f))
    log.info('Config init')
