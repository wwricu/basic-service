import asyncio
import atexit
import os.path
import pickle
import time
from typing import Protocol

import redis.asyncio as redis
from loguru import logger as log
from sqlalchemy import Integer, String, BLOB, select, delete, update, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import Mapped, mapped_column, Session

from wwricu.config import RedisConfig
from wwricu.domain.entity import Base
from wwricu.domain.common import EntityConstant


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
        if second is None or second <= 0:
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
        if second is None or second <= 0:
            second = 600
        if value is not None:
            value = pickle.dumps(value)
        await self.redis.set(key, value, ex=second)

    async def delete(self, key: str):
        await self.redis.delete(key)


class SqliteCache:
    engine: AsyncEngine

    class CacheTable(Base):
        __tablename__ = 'cache'
        id: Mapped[int] = mapped_column(Integer(), primary_key=True)
        key: Mapped[str] = mapped_column(String(EntityConstant.LONG_STRING_LEN), unique=True, nullable=False)
        value: Mapped[bytes] = mapped_column(BLOB, unique=True, nullable=True)
        expire: Mapped[int] = mapped_column(Integer(), nullable=True)

    def __init__(self):
        database: str = 'cache.sqlite'
        self.engine = create_async_engine(f'sqlite+aiosqlite:///{database}', echo=__debug__)
        engine = create_engine(f'sqlite:///{database}', echo=__debug__)
        self.CacheTable.metadata.create_all(engine)
        with Session(engine) as session, session.begin():
            stmt = delete(self.CacheTable).where(self.CacheTable.expire < int(time.time()))
            session.execute(stmt)

    async def get(self, key: str) -> any:
        async with AsyncSession(self.engine) as session, session.begin():
            stmt = select(self.CacheTable).where(self.CacheTable.key == key)
            if (value := (await session.execute(stmt)).fetchone()) is None:
                return None
            if value.expire is not None and value.expire < int(time.time()):
                return None
            return pickle.loads(value.value)

    async def set(self, key: str, value: any, second: int):
        if second is None or second <= 0:
            second = 600
        if value is not None:
            value = pickle.dumps(value)
        async with AsyncSession(self.engine) as session, session.begin():
            stmt = select(self.CacheTable).where(self.CacheTable.key == key)
            if await session.scalar(stmt) is not None:
                stmt = update(self.CacheTable).where(self.CacheTable.key == key).values(
                    value=pickle.dumps(value),
                    expire=int(time.time()) + second
                )
                await session.execute(stmt)
            else:
                session.add(self.CacheTable(key=key, value=pickle.dumps(value), expire=int(time.time()) + second))
        if second > 0:
            asyncio.create_task(self.timeout(key, second))

    async def delete(self, key: str):
        async with AsyncSession(self.engine) as session, session.begin():
            stmt = select(self.CacheTable).where(self.CacheTable.key == key)
            if await session.scalar(stmt) is not None:
                stmt = delete(self.CacheTable).where(self.CacheTable.key == key)
                await session.execute(stmt)

    async def timeout(self, key: str, second: int):
        await asyncio.sleep(second)
        await self.delete(key)


class Cache(Protocol):
    async def get(self, key: str) -> any:
        pass

    async def set(self, key: str, value: any, second: int):
        pass

    async def delete(self, key: str):
        pass


cache: Cache = LocalCache()
