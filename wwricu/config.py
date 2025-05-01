import json
import logging
import os
import sys

import boto3
from loguru import logger as log

from wwricu.domain.constant import CommonConstant
from wwricu.domain.enum import EnvironmentEnum
from wwricu.domain.third import AWSConst, AWSAppConfigSessionResponse, AWSAppConfigConfigResponse


class ConfigClass(object):
    @classmethod
    def init(cls, **kwargs):
        for k, v in kwargs.items():
            if k in cls.__annotations__:
                setattr(cls, k, v)
        cls.__new__(cls)


class StorageConfig(ConfigClass):
    region: str
    bucket: str
    private_bucket: str


class DatabaseConfig(ConfigClass):
    async_driver: str = ''
    sync_driver: str = ''
    username: str = ''
    password: str = ''
    host: str = ''
    port: int = 0
    database: str = ''
    url: str | None = None
    sync_url: str | None = None

    def __new__(cls):
        connect_string = f'{{driver}}://{cls.username}:{cls.password}@{cls.host}:{cls.port}/{cls.database}'
        if cls.url is None:
            cls.url = connect_string.format(driver=cls.async_driver)
        if cls.sync_url is None:
            cls.sync_url = connect_string.format(driver=cls.sync_driver)
        log.info(f'async connect string = {cls.url}')
        log.info(f'sync connect string = {cls.sync_url}')


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
    version: str = '0.0.0'
    encoding: str = 'utf-8'
    trash_expire_day: int = 30

    @classmethod
    def load(
        cls,
        admin_config: dict,
        database_config: dict,
        storage_config: dict,
        redis_config: dict | None = None,
        **kwargs
    ):
        cls.init(**kwargs)
        if os.path.exists(CommonConstant.VERSION_FILE):
            with open(CommonConstant.VERSION_FILE) as f:
                cls.version = f.read().strip()
        AdminConfig.init(**admin_config)
        DatabaseConfig.init(**database_config)
        StorageConfig.init(**storage_config)
        if redis_config:
            RedisConfig.init(**redis_config)


def log_config():
    logging.Logger.manager.loggerDict.clear()
    log.remove()
    if __debug__:
        log.add(sys.stdout, level=logging.DEBUG)
    os.makedirs(CommonConstant.LOG_PATH, exist_ok=True)
    log.add(f'{CommonConstant.LOG_PATH}/server.log', level=logging.DEBUG, rotation='monday at 00:00')


def get_config(env: EnvironmentEnum) -> dict:
    log.info(f'env={env.value}')
    if env == EnvironmentEnum.LOCAL:
        with open(CommonConstant.CONFIG_FILE) as f:
            return json.loads(f.read())
    log.warning(f'Getting config from {AWSConst.APP_CONFIG_DATA}')
    app_config_data_client = boto3.client(AWSConst.APP_CONFIG_DATA, region_name=AWSConst.REGION)
    response = app_config_data_client.start_configuration_session(
        ApplicationIdentifier=CommonConstant.APP_NAME,
        EnvironmentIdentifier=env,
        ConfigurationProfileIdentifier=CommonConstant.CONFIG_FILE
    )
    aws_session = AWSAppConfigSessionResponse.model_validate(response)
    response = app_config_data_client.get_latest_configuration(ConfigurationToken=aws_session.InitialConfigurationToken)
    app_config = AWSAppConfigConfigResponse.model_validate(response)
    content = app_config.Configuration.read().decode()
    app_config.Configuration.close()
    return json.loads(content)


def init():
    log_config()
    if __debug__:
        log.warning('APP RUNNING ON DEBUG MODE')
    env = os.getenv(CommonConstant.ENV_KEY, EnvironmentEnum.LOCAL.value)
    Config.load(**get_config(EnvironmentEnum(env)))
    if os.path.exists(CommonConstant.VERSION_FILE):
        with open(CommonConstant.VERSION_FILE) as f:
            Config.version = f.read().strip()
    log.info('Config init')
