import json
import logging
import os
import sys
from pathlib import Path

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
    log_path = EnvVarEnum.LOG_PATH.get()
    os.makedirs(log_path, exist_ok=True)
    log.add(f'{log_path}/server.log', level=logging.DEBUG, rotation='monday at 00:00')
    log.add(
        f'{log_path}/access.log',
        level=logging.NOTSET,
        filter=lambda record: record.get('level').no < logging.DEBUG,
        rotation='monday at 00:00'
    )


def get_config() -> dict:
    log.info(f'env={Config.env.value}')
    config_file = Path(EnvVarEnum.CONFIG_FILE.get())
    if config_file.exists() and config_file.is_file():
        log.info(f'Getting config from {config_file.absolute()}')
        with config_file.open() as f:
            return json.loads(f.read())

    log.warning(f'Getting config from {AWSConst.APP_CONFIG_DATA}')
    app_config_data_client = boto3.client(AWSConst.APP_CONFIG_DATA, region_name=AWSConst.REGION)
    response = app_config_data_client.start_configuration_session(
        ApplicationIdentifier=CommonConstant.APP_NAME,
        EnvironmentIdentifier=Config.env,
        ConfigurationProfileIdentifier=config_file.name
    )
    aws_session = AWSAppConfigSessionResponse.model_validate(response)
    # PRICED call on each deployment
    response = app_config_data_client.get_latest_configuration(ConfigurationToken=aws_session.InitialConfigurationToken)
    app_config = AWSAppConfigConfigResponse.model_validate(response)
    content = app_config.Configuration.read().decode()
    app_config.Configuration.close()

    config_file.parent.mkdir(parents=True, exist_ok=True)
    with config_file.open('wt+') as f:
        f.write(content)
    return json.loads(content)


def init():
    log_config()
    if __debug__:
        log.warning('APP RUNNING ON DEBUG MODE')
    Config.load(**get_config())
    log.info('Config init')
