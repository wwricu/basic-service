import asyncio
import pickle
import time
from typing import Any, Protocol

import redis.asyncio as redis
from loguru import logger as log
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from wwricu.config import DatabaseConfig, RedisConfig
from wwricu.domain.entity import SysCache, sys_cache_base


class LocalCache:
    # DO NOT init class variables so that they will not be inited when the class is not instantiated
    cache_data: dict[str, Any]
    cache_timeout: dict[str, int]
    timeout_callback: dict[str, asyncio.Task]

    def __init__(self):
        self.cache_data = dict()
        self.cache_timeout = dict()
        self.timeout_callback = dict()

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

    async def init(self):
        log.info('Load cache data')
        engine = create_async_engine(DatabaseConfig.cache_url)
        try:
            async with engine.begin() as conn:
                await conn.run_sync(sys_cache_base.metadata.create_all)
            now = int(time.time())
            async with AsyncSession(engine) as s:
                result = (await s.scalars(select(SysCache))).all()
                for c in result:
                    if c.expire > now:
                        await self.set(c.key, c.value, c.expire - now)
                log.info(f'{len(result)} cache entries loaded')
        finally:
            async with AsyncSession(engine) as s:
                await s.execute(delete(SysCache))

    async def close(self):
        log.info('Dump cache data')
        engine = create_async_engine(DatabaseConfig.cache_url)
        async with AsyncSession(engine) as s, s.begin():
            await s.execute(delete(SysCache))
            for key, value in self.cache_data.items():
                if task := self.timeout_callback.pop(key, None):
                    task.cancel()
                s.add(SysCache(key=key, value=pickle.dumps(value), expire=self.cache_timeout.get(key, 0)))


class RedisCache:
    redis: redis.Redis

    async def init(self):
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
    async def init(self):...

    async def get(self, key: str) -> any:...

    async def set(self, key: str, value: any, second: int = 600):...

    async def delete(self, key: str):...

    async def close(self):...


cache: Cache = LocalCache()
