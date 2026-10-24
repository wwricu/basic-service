import logging
import os
import sys
from pathlib import Path

import cloudflare
from dotenv import load_dotenv
from loguru import logger as log
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from wwricu.domain.enum import EnvironmentEnum


class StorageConfig(BaseModel):
    bucket: str
    access_key_id: str = ''
    secret_access_key: str = ''


class DatabaseConfig(BaseModel):
    driver: str
    username: str = ''
    password: str = ''
    host: str = ''
    port: int = 0
    database: str

    @property
    def url(self):
        return f'{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'


class SecurityConfig(BaseModel):
    username: str
    password: str
    secret_key: str
    login_ip_times: int = Field(3, gt=0)
    login_ip_span: float = Field(1800.0, gt=0)


class Config(BaseSettings):
    max_upload_size: int = 10 * 1024 * 1024

    storage: StorageConfig
    database: DatabaseConfig
    security: SecurityConfig


class EnvironmentVariable(BaseSettings):
    ENV: EnvironmentEnum = EnvironmentEnum.DEVELOPMENT
    BASE_DOMAIN: str = 'wwr.icu'
    LOG_PATH: str = 'logs'
    CONFIG_FILE: str = 'config.json'
    VERSION: str = '0.0.1'

    CF_ACCOUNT_ID: str = ''
    CF_KV_NAMESPACE_ID: str = ''
    CF_KV_API_TOKEN: str = ''

    @property
    def resource_domain(self):
        return f'res.{self.BASE_DOMAIN}'


def init_log():
    logging.Logger.manager.loggerDict.clear()
    log.remove()

    if __debug__:
        log.add(sys.stdout, level=logging.NOTSET, backtrace=False)
        log.warning('APP RUNNING ON DEBUG MODE')

    os.makedirs(env.LOG_PATH, exist_ok=True)
    log.add(f'{env.LOG_PATH}/error.log', level=logging.ERROR, rotation='1 MB', retention=10, backtrace=False)
    log.add(f'{env.LOG_PATH}/server.log', level=logging.DEBUG, rotation='10 MB', retention=10, backtrace=False)
    log.add(
        f'{env.LOG_PATH}/access.log',
        level=logging.NOTSET,
        filter=lambda record: record.get('level').no < logging.DEBUG,
        rotation='20 MB',
        retention=10
    )


def init_config() -> Config:
    log.info(f'env={env.ENV}')
    log.info(f'{sys.version=}')
    config_file = Path(env.CONFIG_FILE)
    if config_file.exists() and config_file.is_file():
        log.info(f'Getting config from {config_file.absolute()}')
        with config_file.open() as f:
            return Config.model_validate_json(f.read())

    log.info(f'Getting config from Cloudflare KV key={config_file.name}')
    if not (env.CF_ACCOUNT_ID and env.CF_KV_NAMESPACE_ID and env.CF_KV_API_TOKEN):
        raise RuntimeError('Cloudflare KV credentials are not configured')

    client = cloudflare.Cloudflare(api_token=env.CF_KV_API_TOKEN)
    try:
        content = client.kv.namespaces.values.get(
            config_file.name,
            account_id=env.CF_ACCOUNT_ID,
            namespace_id=env.CF_KV_NAMESPACE_ID,
        ).read().decode()
    except cloudflare.APIStatusError:
        log.error('Failed to get config from Cloudflare KV')
        raise

    config_file.parent.mkdir(parents=True, exist_ok=True)
    with config_file.open('wt+') as f:
        f.write(content)
    return Config.model_validate_json(content)


load_dotenv()
env = EnvironmentVariable()
init_log()
app_config = init_config()
