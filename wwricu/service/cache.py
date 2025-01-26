import asyncio
import pickle
import time

import redis.asyncio as redis
from loguru import logger as log

from wwricu.config import RedisConfig


class LocalCache:
    cache_data: dict[str, any] = dict()
    cache_timeout: dict[str, int] = dict()
    timeout_callback: dict[str, asyncio.Task] = dict()

    async def timeout(self, key: str, second: int):
        await asyncio.sleep(second)
        await self.delete(key)

    async def get(self, key: str) -> any:
        if 0 < self.cache_timeout.get(key, 0) < int(time.time()):
            return None
        return self.cache_data.get(key)

    async def set(self, key: str, value: any, second: int):
        if second is None or second <= 0:
            second = 600
        if task := self.timeout_callback.pop(key, None):
            task.cancel()
        self.cache_data[key] = value
        if second > 0:
            self.timeout_callback[key] = asyncio.create_task(self.timeout(key, second))
            self.cache_timeout[key] = int(time.time()) + second

    async def delete(self, key: str):
        self.cache_data.pop(key)
        self.cache_timeout.pop(key)
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
        if value is not None:
            value = pickle.dumps(value)
        await self.redis.set(key, value, ex=second)

    async def delete(self, key: str):
        await self.redis.delete(key)


class Cache:
    redis_client: RedisCache
    local_cache: LocalCache

    def __init__(self):
        self.redis_client = RedisCache()
        self.local_cache = LocalCache()

    async def get(self, key: str) -> any:
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            log.warning(f'Get cache key {key} from local cache {e}')
            return await self.local_cache.get(key)

    async def set(self, key: str, value: any, second: int = 600):
        try:
            await self.redis_client.set(key, value, second)
        except Exception as e:
            log.warning(f'Set cache key {key} to local cache {e}')
            return await self.local_cache.set(key, value, second)

    async def delete(self, key: str):
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            log.warning(f'Delete cache key {key} from local cache {e}')
            return await self.local_cache.delete(key)


cache = Cache()
