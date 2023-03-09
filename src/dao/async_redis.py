from __future__ import annotations
import asyncio
import pickle
from threading import Lock
from typing import Awaitable, cast

from redis.asyncio import ConnectionPool, StrictRedis

from config import Config, logger


class AsyncRedis(StrictRedis):
    __pool: ConnectionPool = None

    # override two methods below ONLY for type hint
    async def set(self, *args, **kwargs) -> bool | None:
        return await cast(Awaitable, super().set(*args, **kwargs))

    async def delete(self, *args):
        await cast(Awaitable, super().delete(*args))

    @classmethod
    async def init_redis(cls):
        try:
            cls.__pool = ConnectionPool(**Config.redis.__dict__)
        except (Exception,):
            Config.redis = None  # switch to memory storage
            logger.warn('failed to connect to redis')

        redis = await cls.get_connection()
        await redis.set('preview_dict', pickle.dumps(dict()))
        await redis.set('count_dict', pickle.dumps(dict()))
        logger.info('redis connected')

    @classmethod
    async def get_connection(cls) -> AsyncRedis:
        if Config.redis is None:
            return FakeRedis.get_instance()
        return AsyncRedis(connection_pool=cls.__pool)

    @classmethod
    async def close_connection(cls):
        if cls.__pool is not None:
            await cls.__pool.disconnect()


class FakeRedis(AsyncRedis):
    __data: dict[str, bytes | None] = dict()
    __lock: Lock = Lock()
    __instance: FakeRedis = None

    @classmethod
    def get_instance(cls):
        cls.__lock.acquire()
        if cls.__instance is None:
            cls.__instance = cls()
        cls.__lock.release()
        return cls.__instance

    async def get(self, key: str, *args, **kwargs):
        _, _ = args, kwargs
        return self.__data.get(key)

    async def set(
        self,
        key: str,
        value: str | bytes,
        *args,
        ex: int | None = 0,
        **kwargs
    ):
        _, _ = args, kwargs
        if isinstance(value, str):
            value = value.encode()
        with self.__lock:
            self.__data[key] = value
        if ex > 0:
            asyncio.create_task(self.delete_timer(key, ex))

    async def delete(self, key: str, *args, **kwargs):
        _, _ = args, kwargs
        with self.__lock:
            self.__data[key] = None

    async def delete_timer(self, key: str, seconds: int):
        await asyncio.sleep(seconds)
        await self.delete(key)
