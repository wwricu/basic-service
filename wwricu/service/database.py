import os
from asyncio import current_task
from contextlib import asynccontextmanager

from loguru import logger as log
from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker, create_async_engine, AsyncSession

from wwricu.service.storage import get_object, put_object
from wwricu.config import DatabaseConfig, StorageConfig


async def open_session() -> AsyncSession:
    try:
        yield session
    finally:
        if session.registry.registry:
            await session.commit()
            await session.remove()


@asynccontextmanager
async def new_session() -> AsyncSession:
    async with AsyncSession(engine) as s, s.begin():
        yield s


def database_init():
    if os.path.exists(DatabaseConfig.database):
        return
    if database := get_object(DatabaseConfig.database, bucket=StorageConfig.private_bucket):
        log.info(f'Download database as {DatabaseConfig.database}')
        with open(DatabaseConfig.database, mode='wb+') as f:
            f.write(database)


def database_backup():
    if not os.path.exists(DatabaseConfig.database):
        return
    with open(DatabaseConfig.database, mode='rb') as f:
        put_object(DatabaseConfig.database, f.read(), StorageConfig.private_bucket)


def database_restore():
    if os.path.exists(DatabaseConfig.database):
        os.remove(DatabaseConfig.database)
    if database := get_object(DatabaseConfig.database, bucket=StorageConfig.private_bucket):
        log.info(f'Download database as {DatabaseConfig.database}')
        with open(DatabaseConfig.database, mode='wb+') as f:
            f.write(database)


if not os.path.exists(DatabaseConfig.database):
    database_restore()
engine = create_async_engine(DatabaseConfig.url, echo=__debug__)
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
session = async_scoped_session(session_maker, scopefunc=current_task)
