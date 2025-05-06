import asyncio
import base64
import pickle
import time
from typing import Any, Protocol

import redis.asyncio as redis
from loguru import logger as log
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from wwricu.config import RedisConfig
from wwricu.domain.enum import ConfigKeyEnum
from wwricu.domain.entity import SysConfig
from wwricu.service.database import sync_engine


class LocalCache:
    # DO NOT init class variables so that they will not be inited when the class is not instantiated
    cache_data: dict[str, Any]
    cache_timeout: dict[str, int]
    timeout_callback: dict[str, asyncio.Task]

    def __init__(self):
        self.cache_data = dict()
        self.cache_timeout = dict()
        self.timeout_callback = dict()
        try:
            self.load()
        finally:
            # delete persist cache after loaded
            stmt = delete(SysConfig).where(SysConfig.key == ConfigKeyEnum.CACHE_DATA)
            with Session(sync_engine) as sync_session:
                sync_session.execute(stmt)

    def load(self):
        log.info('Load cache data')
        stmt = select(SysConfig).where(SysConfig.key == ConfigKeyEnum.CACHE_DATA).where(SysConfig.deleted == False)
        with Session(sync_engine) as sync_session:
            cache_data_config = sync_session.scalar(stmt)
            if cache_data_config is None or cache_data_config.value is None:
                return
            self.cache_data, self.cache_timeout = pickle.loads(base64.b64decode(cache_data_config.value))
        now = int(time.time())
        for key, value in self.cache_data.items():
            if (second := self.cache_timeout.get(key, 0) - now) > 0:
                self.cache_data[key] = value
                self.cache_timeout[key] = now + second

    async def timeout(self, key: str, second: int):
        await asyncio.sleep(second)
        await self.delete(key)

    async def get(self, key: str) -> any:
        if key is None:
            return None
        if not isinstance(key, str):
            raise ValueError(key)
        if 0 < self.cache_timeout.get(key, 0) < int(time.time()):
            self.cache_data.pop(key, None)
            self.cache_timeout.pop(key, None)
            return None
        return self.cache_data.get(key)

    async def set(self, key: str, value: any, second: int = 600):
        if key is None:
            return
        if not isinstance(key, str):
            raise ValueError(key)
        if task := self.timeout_callback.pop(key, None):
            task.cancel()
        self.cache_data[key] = value
        if second > 0:
            self.timeout_callback[key] = asyncio.create_task(self.timeout(key, second))
            self.cache_timeout[key] = int(time.time()) + second

    async def delete(self, key: str):
        self.cache_data.pop(key, None)
        self.cache_timeout.pop(key, None)
        if task := self.timeout_callback.pop(key, None):
            task.cancel()

    async def close(self):
        # TODO: lengthy cache
        log.info('Dump cache data')
        stmt = delete(SysConfig).where(SysConfig.key == ConfigKeyEnum.CACHE_DATA)
        with Session(sync_engine) as sync_session, sync_session.begin():
            sync_session.execute(stmt)
            sync_session.add(SysConfig(
                key=ConfigKeyEnum.CACHE_DATA,
                value=base64.b64encode(pickle.dumps((self.cache_data, self.cache_timeout))).decode(),
            ))


class RedisCache:
    redis: redis.Redis

    def __init__(self):
        self.redis = redis.Redis(
            username=RedisConfig.username,
            password=RedisConfig.password,
            host=RedisConfig.host,
            port=RedisConfig.port
        )

    async def get(self, key: str) -> any:
        value = await self.redis.get(key)
        return None if value is None else pickle.loads(value)

    async def set(self, key: str, value: any, second: int = 600):
        if value is not None:
            value = pickle.dumps(value)
        await self.redis.set(key, value, ex=second)

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def close(self):
        await self.redis.close()


class Cache(Protocol):
    async def get(self, key: str) -> any:...

    async def set(self, key: str, value: any, second: int = 600):...

    async def delete(self, key: str):...

    async def close(self):...


cache: Cache = LocalCache()
