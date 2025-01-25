import abc
import asyncio
import os
import pickle
import time

import redis  # aioredis is not ready for python3.12 yet

from wwricu.config import RedisConfig
from wwricu.domain.common import CommonConstant


class CacheService(abc.ABC):
    @abc.abstractmethod
    async def get(self, key: str) -> any:
        pass

    @abc.abstractmethod
    async def set(self, key: str, value: any, second: int):
        pass

    @abc.abstractmethod
    async def delete(self, key: str):
        pass


async def timeout(key: str, second: int):
    await asyncio.sleep(second)
    await cache_delete(key)


async def cache_delete(key: str):
    cache_data.pop(key)
    cache_timeout.pop(key)
    if task := timeout_callback.pop(key, None):
        task.cancel()


async def cache_set(key: str, value: any, second: int = 600):
    if second is None or second <= 0:
        second = 600
    if task := timeout_callback.pop(key, None):
        task.cancel()
    cache_data[key] = value
    if second > 0:
        timeout_callback[key] = asyncio.create_task(timeout(key, second))
        cache_timeout[key] = int(time.time()) + second


async def cache_get(key: str) -> any:
    if 0 < cache_timeout.get(key, 0) < int(time.time()):
        return None
    return cache_data.get(key)


async def cache_dump():
    with open(CommonConstant.CACHE_DUMP_FILE, 'wb+') as f:
        f.write(pickle.dumps((cache_data, cache_timeout)))


async def cache_load():
    if not os.path.exists(CommonConstant.CACHE_DUMP_FILE):
        return
    with open(CommonConstant.CACHE_DUMP_FILE, 'rb') as f:
        persist_data, persist_timeout = pickle.loads(f.read())
    now = int(time.time())
    for key, value in persist_data.items():
        if (second := persist_timeout.get(key, 0) - now) > 0:
            await cache_set(key, value, second)
    os.remove(CommonConstant.CACHE_DUMP_FILE)


class RedisCache(CacheService):
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
        if value is not None:
            value = pickle.dumps(value)
        await self.redis.set(key, value)

    async def delete(self, key: str):
        await self.redis.delete(key)


cache: CacheService = RedisCache()



cache_data: dict[str, any] = dict()
cache_timeout: dict[str, int] = dict()
timeout_callback: dict[str, asyncio.Task] = dict()
