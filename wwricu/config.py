import json
import logging
import os
import sys

import boto3
from loguru import logger as log

from wwricu.domain.constant import CommonConstant
from wwricu.domain.enum import EnvironmentEnum
from wwricu.domain.third import AWSAppConfigResponse, AWSConst


class ConfigClass(object):
    @classmethod
    def init(cls, **kwargs):
        for k, v in kwargs.items():
            if k in cls.__annotations__:
                setattr(cls, k, v)


class StorageConfig(ConfigClass):
    region: str
    bucket: str
    private_bucket: str


class DatabaseConfig(ConfigClass):
    url: str
    database: str


class RedisConfig(ConfigClass):
    host: str
    port: int
    username: str
    password: str


class AdminConfig(ConfigClass):
    username: str
    password: str
    secure_key: str


class Config(ConfigClass):
    host: str = '0.0.0.0'
    port: int = 8000
    log_level: int = logging.CRITICAL
    encoding: str = 'utf-8'
    version: str = 'NO VERSION'
    trash_expire_day: int = 30

    @classmethod
    def load(cls, admin_config: dict, database_config: dict, storage_config: dict, redis_config: dict, **kwargs):
        cls.init(**kwargs)
        if os.path.exists(CommonConstant.VERSION_FILE):
            with open(CommonConstant.VERSION_FILE) as f:
                cls.version = f.read().strip()
        AdminConfig.init(**admin_config)
        DatabaseConfig.init(**database_config)
        StorageConfig.init(**storage_config)
        RedisConfig.init(**redis_config)


def log_config():
    logging.Logger.manager.loggerDict.clear()
    log.remove()
    if __debug__:
        log.add(sys.stdout, level=logging.DEBUG)
    os.makedirs(CommonConstant.LOG_PATH, exist_ok=True)
    log.add(f'{CommonConstant.LOG_PATH}/{{time:YYYY-MM-DD}}.log', level=logging.INFO, rotation='00:00')


def get_config(env: EnvironmentEnum) -> dict:
    log.info(f'env={env.value}')
    if env == EnvironmentEnum.LOCAL:
        with open(CommonConstant.CONFIG_FILE) as f:
            return json.loads(f.read())
    response = boto3.client(AWSConst.APP_CONFIG, region_name=AWSConst.REGION).get_configuration(
        Application=CommonConstant.APP_NAME,
        Environment=env,
        Configuration=CommonConstant.CONFIG_FILE,
        ClientId=CommonConstant.APP_NAME
    )
    app_config = AWSAppConfigResponse.model_validate(response)
    content = app_config.Content.read().decode()
    app_config.Content.close()
    return json.loads(content)


def init():
    log_config()
    if __debug__:
        log.warning('APP RUNNING ON DEBUG MODE')
    env = os.getenv(CommonConstant.ENV_KEY, EnvironmentEnum.LOCAL.value)
    Config.load(**get_config(EnvironmentEnum(env)))
    log.info('Config init')
