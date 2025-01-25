import json
import logging
import os
import sys
from logging import CRITICAL
from types import FrameType
from typing import cast

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
    bucket: str
    private_bucket: str


class DatabaseConfig(ConfigClass):
    url: str
    database: str
    dynamo_region: str = 'OREGON'


class RedisConfig(ConfigClass):
    host: str
    port: int
    username: str
    password: str


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
    def load(cls, admin_config: dict, database_config: dict, storage_config: dict, redis_config: dict, **kwargs):
        cls.init(**kwargs)
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


def download_config():
    ssm_client = boto3.client(AWSConst.ssm, region_name=AWSConst.region)
    content = ssm_client.get_parameter(Name=AWSConst.config_key, WithDecryption=False)
    response = AWSSSMResponse.model_validate(content)
    with open(CommonConstant.CONFIG_FILE, 'wt+') as f:
        f.write(response.Parameter.Value)


def init():
    log_config()
    if __debug__:
        log.warning('APP RUNNING ON DEBUG MODE')
    try:
        download_config()
        log.info(f'Downloaded config file as {CommonConstant.CONFIG_FILE}')
    except Exception as e:
        log.warning(f'Failed to download config: {e}, load locally')
    with open(CommonConstant.CONFIG_FILE) as f:
        Config.load(**json.load(f))
    log.info('Config init')
