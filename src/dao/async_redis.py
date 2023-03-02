from __future__ import annotations
import pickle
from threading import Lock
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
            return cast(Redis, FakeRedis.get_instance())
        return StrictRedis(connection_pool=cls.__pool)

    @classmethod
    async def close(cls):
        await cls.__pool.disconnect()


class FakeRedis:
    __data: dict[str, bytes | None] = None
    __lock: Lock = Lock()
    __instance: FakeRedis = None

    @classmethod
    def get_instance(cls):
        cls.__lock.acquire()
        if cls.__instance is None:
            instance = cls()
            instance.__lock = Lock()
            instance.__data = dict()
            instance.__data.setdefault('count_dict', pickle.dumps(dict()))
            instance.__data.setdefault('preview_dict', pickle.dumps(dict()))
            cls.__instance = instance
        cls.__lock.release()
        return cls.__instance

    async def get(self, key: str, *args, **kwargs):
        _, _ = args, kwargs
        return self.__data.get(key)

    async def set(self, key: str, value: str | bytes, *args, **kwargs):
        _, _ = args, kwargs
        self.__lock.acquire()
        if isinstance(value, str):
            value = value.encode()
        self.__data[key] = value
        self.__lock.release()

    async def delete(self, key: str, *args, **kwargs):
        _, _ = args, kwargs
        self.__lock.acquire()
        self.__data[key] = None
        self.__lock.release()
