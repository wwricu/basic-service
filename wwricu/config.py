import json
import logging
import os
import sys

import boto3
from loguru import logger as log

from wwricu.domain.constant import CommonConstant
from wwricu.domain.enum import EnvironmentEnum, EnvVarEnum
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
    env: EnvironmentEnum = EnvironmentEnum(EnvVarEnum.ENV.get())

    @classmethod
    def is_local(cls) -> bool:
        return cls.env == EnvironmentEnum.LOCAL

    @classmethod
    def not_local(cls) -> bool:
        return not cls.is_local()

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
    os.makedirs(EnvVarEnum.LOG_PATH.get(), exist_ok=True)
    log.add(f'{EnvVarEnum.LOG_PATH.get()}/server.log', level=logging.DEBUG, rotation='monday at 00:00')


def get_config() -> dict:
    log.info(f'env={Config.env.value}')
    if os.path.exists(CommonConstant.CONFIG_FILE):
        with open(CommonConstant.CONFIG_FILE) as f:
            return json.loads(f.read())
    log.warning(f'Getting config from {AWSConst.APP_CONFIG_DATA}')
    app_config_data_client = boto3.client(AWSConst.APP_CONFIG_DATA, region_name=AWSConst.REGION)
    response = app_config_data_client.start_configuration_session(
        ApplicationIdentifier=CommonConstant.APP_NAME,
        EnvironmentIdentifier=Config.env,
        ConfigurationProfileIdentifier=CommonConstant.CONFIG_FILE
    )
    aws_session = AWSAppConfigSessionResponse.model_validate(response)
    # This is a PRICED call, called on each deployment
    response = app_config_data_client.get_latest_configuration(ConfigurationToken=aws_session.InitialConfigurationToken)
    app_config = AWSAppConfigConfigResponse.model_validate(response)
    content = app_config.Configuration.read().decode()
    app_config.Configuration.close()
    with open(CommonConstant.CONFIG_FILE, 'wt+') as f:
        f.write(content)
    return json.loads(content)


def init():
    log_config()
    if __debug__:
        log.warning('APP RUNNING ON DEBUG MODE')
    Config.load(**get_config())
    if os.path.exists(CommonConstant.VERSION_FILE):
        with open(CommonConstant.VERSION_FILE) as f:
            Config.version = f.read().strip()
    log.info('Config init')
