import asyncio
import atexit
import os.path
import pickle
import time
from typing import Protocol

import redis.asyncio as redis
from loguru import logger as log

from wwricu.config import RedisConfig


class LocalCache:
    # DO NOT init class variables so that they will not be inited when the class is not instantiated
    cache_data: dict[str, any]
    cache_timeout: dict[str, int]
    timeout_callback: dict[str, asyncio.Task]
    cache_name: str = 'cache.pkl'

    def __init__(self):
        atexit.register(self.cache_dump)
        self.cache_data = dict()
        self.cache_timeout = dict()
        self.timeout_callback = dict()
        self.cache_load()


    def cache_load(self):
        if not os.path.exists(self.cache_name):
            return
        log.info('Load cache from pickle')
        with open(self.cache_name, 'rb') as f:
            self.cache_data, self.cache_timeout = pickle.loads(f.read())
        now = int(time.time())
        for key, value in self.cache_data.items():
            if (second := self.cache_timeout.get(key, 0) - now) > 0:
                self.cache_data[key] = value
                self.cache_timeout[key] = now + second

    def cache_dump(self):
        log.info('Dump cache to pickle')
        with open(self.cache_name, 'wb+') as f:
            f.write(pickle.dumps((self.cache_data, self.cache_timeout)))

    async def timeout(self, key: str, second: int):
        await asyncio.sleep(second)
        await self.delete(key)

    async def get(self, key: str) -> any:
        if 0 < self.cache_timeout.get(key, 0) < int(time.time()):
            self.cache_data.pop(key, None)
            self.cache_timeout.pop(key, None)
            return None
        return self.cache_data.get(key)

    async def set(self, key: str, value: any, second: int):
        if second is None or second < 0:
            second = 600
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
        if value is not None:
            return pickle.loads(value)

    async def set(self, key: str, value: any, second: int):
        if second is None or second < 0:
            second = 600
        if value is not None:
            value = pickle.dumps(value)
        await self.redis.set(key, value, ex=second)

    async def delete(self, key: str):
        await self.redis.delete(key)


class Cache(Protocol):
    async def get(self, key: str) -> any:...

    async def set(self, key: str, value: any, second: int):...

    async def delete(self, key: str):...


cache: Cache = LocalCache()
