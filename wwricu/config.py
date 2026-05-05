import logging
import os
import sys
import uuid
from pathlib import Path

import boto3
from dotenv import load_dotenv
from loguru import logger as log
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from wwricu.domain.constant import CommonConstant
from wwricu.domain.enum import EnvironmentEnum
from wwricu.domain.third import AWSConst, AWSAppConfigSessionResponse, AWSAppConfigConfigResponse


class StorageConfig(BaseModel):
    region: str
    bucket: str
    private_bucket: str


class DatabaseConfig(BaseModel):
    driver: str
    username: str = ''
    password: str = ''
    host: str = ''
    port: int = 0
    database: str = ''

    @property
    def url(self):
        return f'{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'


class Throttle(BaseModel):
    name: str = Field(default_factory=lambda: uuid.uuid4().hex)
    enable: bool = True
    qps: float
    capacity: float


class ThrottleConfig(BaseModel):
    login_ip: Throttle = Throttle(qps=1, capacity=5)
    login_global: Throttle = Throttle(qps=10, capacity=50)
    open_ip: Throttle = Throttle(qps=20, capacity=100)


class SecurityConfig(BaseModel):
    username: str
    password: str
    secret_key: str
    throttle: ThrottleConfig = ThrottleConfig()


class Config(BaseSettings):
    encoding: str = 'utf-8'
    trash_expire_day: int = 30
    max_upload_size: int = 10 * 1024 * 1024

    storage: StorageConfig
    database: DatabaseConfig
    security: SecurityConfig


class EnvironmentVariable(BaseSettings):
    ENV: EnvironmentEnum = EnvironmentEnum.LOCAL
    RESOURCE_HOSTNAME: str = 'res.wwr.icu'
    ROOT_PATH: str = '/'
    LOG_PATH: str = 'logs'
    CONFIG_FILE: str = 'config.json'
    VERSION: str = '0.0.1'


def init_log():
    logging.Logger.manager.loggerDict.clear()
    log.remove()

    if __debug__:
        log.add(sys.stdout, level=logging.NOTSET, backtrace=False)
        log.warning('APP RUNNING ON DEBUG MODE')

    log_path = env.LOG_PATH
    os.makedirs(log_path, exist_ok=True)
    log.add(f'{log_path}/server.log', level=logging.DEBUG, rotation='10 MB', retention=10, backtrace=False)
    log.add(
        f'{log_path}/access.log',
        level=logging.NOTSET,
        filter=lambda record: record.get('level').no < logging.DEBUG,
        rotation='20 MB',
        retention=10
    )


def init_config() -> Config:
    log.info(f'env={env.ENV}')
    config_file = Path(env.CONFIG_FILE)
    if config_file.exists() and config_file.is_file():
        log.info(f'Getting config from {config_file.absolute()}')
        with config_file.open() as f:
            return Config.model_validate_json(f.read())

    log.warning(f'Getting config from {AWSConst.APP_CONFIG_DATA}')
    app_config_data_client = boto3.client(AWSConst.APP_CONFIG_DATA, region_name=AWSConst.REGION)
    response = app_config_data_client.start_configuration_session(
        ApplicationIdentifier=CommonConstant.APP_NAME,
        EnvironmentIdentifier=EnvironmentEnum(env.ENV),
        ConfigurationProfileIdentifier=config_file.name
    )
    aws_session = AWSAppConfigSessionResponse.model_validate(response)
    aws_session.check()

    # PRICED call on each deployment
    response = app_config_data_client.get_latest_configuration(ConfigurationToken=aws_session.InitialConfigurationToken)
    aws_app_config = AWSAppConfigConfigResponse.model_validate(response)
    aws_app_config.check()

    content = aws_app_config.Configuration.read().decode()
    aws_app_config.Configuration.close()

    config_file.parent.mkdir(parents=True, exist_ok=True)
    with config_file.open('wt+') as f:
        f.write(content)
    return Config.model_validate_json(content)


load_dotenv()
env = EnvironmentVariable()
init_log()
app_config = init_config()
