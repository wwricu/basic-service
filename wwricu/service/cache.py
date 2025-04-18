import asyncio
import os.path
import pickle
import time
from typing import Any, Protocol, cast

import redis.asyncio as redis
from loguru import logger as log
from python_multipart.decoders import SupportsWrite

from wwricu.config import RedisConfig


class LocalCache:
    # DO NOT init class variables so that they will not be inited when the class is not instantiated
    cache_data: dict[str, Any]
    cache_timeout: dict[str, int]
    timeout_callback: dict[str, asyncio.Task]
    cache_name: str = 'cache.pkl'

    def __init__(self):
        self.cache_data = dict()
        self.cache_timeout = dict()
        self.timeout_callback = dict()

        if not os.path.exists(self.cache_name):
            return
        log.info('Load cache from pickle')
        with open(self.cache_name, 'rb') as f:
            self.cache_data, self.cache_timeout = pickle.load(f)
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
        log.info('Dump cache to pickle')
        with open(self.cache_name, 'wb+') as f:
            pickle.dump((self.cache_data, self.cache_timeout), cast(SupportsWrite[bytes], f))


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
