import pickle
from typing import Awaitable, cast

from redis.asyncio import ConnectionPool, Redis, StrictRedis

from config import Config, logger


class AsyncRedis:
    __pool: ConnectionPool = None

    @classmethod
    async def init_redis(cls):
        if Config.redis is None or cls.__pool is not None:
            return
        try:
            cls.__pool = ConnectionPool(**Config.redis.__dict__)
        except Exception as e:
            Config.redis = None
            logger.warn('failed to connect to redis', e)

        redis = await cls.get_connection()
        await cast(Awaitable, redis.set('preview_dict', pickle.dumps(dict())))
        await cast(Awaitable, redis.set('count_dict', pickle.dumps(dict())))
        logger.info('redis connected')

    @classmethod
    async def get_connection(cls) -> Redis:
        if Config.redis is None:
            return cast(Redis, FakeRedis())
        return StrictRedis(connection_pool=cls.__pool)

    @classmethod
    async def close(cls):
        await cls.__pool.disconnect()


class FakeRedis:
    async def get(self, key: str):
        _, _ = self, key
        return None

    async def set(self, key: str, value: str):
        _, _, _ = self, key, value
        return None

    async def delete(self, key: str):
        _, _ = self, key
        return None
