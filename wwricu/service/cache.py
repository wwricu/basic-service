import asyncio
import pickle
import shelve
import time
from typing import Protocol

import redis.asyncio as redis
from loguru import logger as log

from wwricu.config import RedisConfig


class LocalCache:
    cache_data: shelve.Shelf
    timeout_callback: dict[str, asyncio.Task]
    cache_name = 'cache'

    def __init__(self):
        self.cache_data = shelve.open(self.cache_name)
        self.timeout_callback = {}
        '''
        NOTE: (... for ... in ...) is a generator expression while [... for ... in ...] is a comprehension
        a generator expression would generate elements on iterating, comprehension create the iteration in advance.
        '''
        for key in [key for key, (_, expire) in self.cache_data.items() if 0 < expire < time.time()]:
            self.cache_data.pop(key, None)
        log.info(f'{len(self.cache_data)} cache entries loaded')

    async def timeout(self, key: str, second: int):
        await asyncio.sleep(second)
        _ = self.timeout_callback.pop(key, None)
        self.cache_data.pop(key, None)

    async def get(self, key: str) -> any:
        if not isinstance(key, str):
            return None
        value, expire = self.cache_data.get(key, (None, 0))
        if 0 < expire < time.time():
            self.cache_data.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: any, second: int = 600):
        if not isinstance(key, str):
            raise ValueError(key)
        if task := self.timeout_callback.pop(key, None):
            task.cancel()

        self.cache_data[key] = value, time.time() + second if second > 0 else 0
        if second > 0:
            self.timeout_callback[key] = asyncio.create_task(self.timeout(key, second))

    async def delete(self, key: str):
        if task := self.timeout_callback.pop(key, None):
            task.cancel()
        self.cache_data.pop(key, None)

    async def close(self):
        self.cache_data.sync()
        log.info(f'{len(self.cache_data)} cache entries dumped')
        self.cache_data.close()


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
