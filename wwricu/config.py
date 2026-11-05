import logging
import os
import sys
from pathlib import Path

import httpx2
from dotenv import load_dotenv
from loguru import logger as log
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from wwricu.domain.enum import EnvironmentEnum
from wwricu.domain.third import CloudflareConst


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
    name: str

    @property
    def url(self):
        return f'{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}'


class SecurityConfig(BaseModel):
    username: str
    password: str
    secret_key: str


class Config(BaseSettings):
    max_upload_size: int = 10 * 1024 * 1024

    storage: StorageConfig
    database: DatabaseConfig
    security: SecurityConfig


class EnvironmentVariable(BaseSettings):
    CF_ACCOUNT_ID: str
    CF_API_TOKEN: str

    ENV: EnvironmentEnum = EnvironmentEnum.DEVELOPMENT
    BASE_DOMAIN: str = 'wwr.icu'
    LOG_PATH: str = 'logs'
    CONFIG_FILE: str = 'dev.config.json'

    @property
    def resource_domain(self) -> str:
        return f'res.{self.BASE_DOMAIN}'

    @property
    def is_dev(self) -> bool:
        return __debug__ or self.ENV != EnvironmentEnum.PRODUCTION


def init_log():
    logging.Logger.manager.loggerDict.clear()
    log.remove()

    if env.is_dev:
        log.add(sys.stdout, level=logging.NOTSET, backtrace=False)
        log.warning('APP RUNNING IN DEV')

    os.makedirs(env.LOG_PATH, exist_ok=True)
    log.add(f'{env.LOG_PATH}/audit.log', level=logging.WARNING, rotation='1 MB', retention=10, backtrace=False)
    log.add(f'{env.LOG_PATH}/server.log', level=logging.DEBUG, rotation='10 MB', retention=10, backtrace=False)
    log.add(
        f'{env.LOG_PATH}/access.log',
        level=logging.NOTSET,
        filter=lambda record: record.get('level').no < logging.DEBUG,
        rotation='20 MB',
        retention=10
    )


def init_config() -> Config:
    log.info(f'{sys.version=}')
    config_file = Path(env.CONFIG_FILE)
    if config_file.exists() and config_file.is_file():
        log.info(f'Getting config from {config_file.absolute()}')
        with config_file.open() as f:
            return Config.model_validate_json(f.read())

    log.info(f'Getting config from Cloudflare KV key={config_file.name}')
    if not env.CF_ACCOUNT_ID or not env.CF_API_TOKEN:
        raise RuntimeError('Cloudflare KV credentials are not configured')

    url = CloudflareConst.KV_ENDPOINT.format(account_id=env.CF_ACCOUNT_ID, key=config_file.name)
    try:
        response = httpx2.get(url, headers=dict(Authorization=f'Bearer {env.CF_API_TOKEN}'))
        response.raise_for_status()
        content = response.text
    except httpx2.HTTPError:
        log.error('Failed to get config from Cloudflare KV')
        raise

    config_file.parent.mkdir(parents=True, exist_ok=True)
    with config_file.open('wt+') as f:
        f.write(content)
    return Config.model_validate_json(content)


load_dotenv()
env = EnvironmentVariable.model_validate(os.environ, extra='ignore')
init_log()
app_config = init_config()
