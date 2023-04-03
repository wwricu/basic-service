from __future__ import annotations
import asyncio
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

    async def hset(self, *args, **kwargs):
        await cast(Awaitable, super().hset(*args, **kwargs))

    @classmethod
    async def init_redis(cls):
        try:
            cls.__pool = ConnectionPool(**Config.redis.__dict__)
        except (Exception,):
            Config.redis = None  # switch to memory storage
            logger.warn('failed to connect to redis')
        logger.info('redis connected')

    @classmethod
    async def get_connection(cls) -> AsyncRedis:
        if Config.redis is None:
            return FakeRedis.get_instance()
        return cls(connection_pool=cls.__pool)

    @classmethod
    async def close_connection(cls):
        # 'close' and 'disconnect' was used by base class
        if cls.__pool is not None:
            await cls.__pool.disconnect()


class FakeRedis(AsyncRedis):
    __data: dict[str, bytes | dict | None] = dict()
    __lock: Lock = Lock()
    __instance: FakeRedis = None

    @classmethod
    def get_instance(cls) -> AsyncRedis:
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

    async def hget(
        self,
        key: str,
        field: str,
        *args,
        **kwargs
    ) -> bytes | None:
        _, _ = args, kwargs
        with self.__lock:
            hash_map: dict[str, bytes | None] = self.__data.get(key)
            return hash_map.get(field) if isinstance(hash_map, dict) else None

    async def hset(
        self,
        key: str,
        field: str,
        value: str | bytes,
        *args,
        **kwargs
    ):
        _, _ = args, kwargs
        self.__lock.acquire()
        if (hash_map := self.__data.get(key)) is None:
            hash_map: dict[str, bytes | None] = dict()
        assert isinstance(hash_map, dict)
        if isinstance(value, str):
            value = value.encode()
        hash_map[field] = value
        self.__data[key] = hash_map
        self.__lock.release()

    async def delete(self, key: str, *args, **kwargs):
        _, _ = args, kwargs
        with self.__lock:
            self.__data[key] = None

    async def delete_timer(self, key: str, seconds: int):
        await asyncio.sleep(seconds)
        await self.delete(key)


class RedisKey:
    BING_IMAGE_URL = 'bing_image_url'
    COUNT_DICT = 'count_dict'
    PREVIEW_DICT = 'preview_dict'

    @staticmethod
    def totp_key(username: str) -> str:
        return f'totp_key:username:{username}'

    @staticmethod
    def two_fa_code(username: str) -> str:
        return f'2fa_code:username:{username}'

    @staticmethod
    def need_2fa(username: str) -> str:
        return f'need_2fa:username:{username}'

    @staticmethod
    def throttle(path: str, method: str, ip: str | int) -> str:
        return f'throttle:url:{path}:method:{method}:ip:{ip}'

    @staticmethod
    def content(content_id: str | int) -> str:
        return f'content:id:{content_id}'

    @staticmethod
    def folder(url: str) -> str:
        return f'folder:url:{url}'

    @staticmethod
    def preview_field(
        url: str,
        category_name: str,
        tag_name: str,
        page_idx: int | str,
        page_size: int | str
    ) -> str:
        return (
            f'preview:url:{url}:'
            + f'category_name:{category_name}:'
            + f'tag_name:{tag_name}:'
            + f'page_idx:{page_idx}:'
            + f'page_size:{page_size}'
        )

    @staticmethod
    def count_field(
        url: str,
        category_name: str,
        tag_name: str,
    ) -> str:
        return 'count:url:{}:category_name:{}:tag_name:{}'.format(
            url,
            category_name,
            tag_name
        )
