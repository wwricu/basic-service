import contextlib
import importlib
import os
from asyncio import current_task
from typing import AsyncGenerator

from loguru import logger as log
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker, create_async_engine

from wwricu.config import DatabaseConfig, StorageConfig
from wwricu.service.storage import oss


async def open_session():
    async with session.begin():
        yield


@contextlib.asynccontextmanager
async def new_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as s, s.begin():
        yield s


@contextlib.asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    scoped_session: AsyncSession = session.registry.registry.get(current_task())
    if scoped_session is not None and scoped_session.is_active and scoped_session.in_transaction():
        yield scoped_session
    else:
        async with new_session() as s:
            yield s


def database_init():
    if os.path.exists(DatabaseConfig.database):
        return
    # This is a PRICED call, called on each deploy
    if database := oss.get(DatabaseConfig.database, bucket=StorageConfig.private_bucket):
        log.warning(f'Download database as {DatabaseConfig.database}')
        with open(DatabaseConfig.database, mode='wb+') as f:
            f.write(database)


def database_backup():
    if not os.path.exists(DatabaseConfig.database):
        return
    log.warning(f'Backup database {DatabaseConfig.database}')
    with open(DatabaseConfig.database, mode='rb') as f:
        # This is a PRICED call, called every week or on each restart
        oss.put(DatabaseConfig.database, f.read(), StorageConfig.private_bucket)
    log.info(f'Backup database success')


async def database_restore():
    if not os.path.exists(DatabaseConfig.database):
        return
    try:
        await session.close_all()
        await engine.dispose()
        os.remove(DatabaseConfig.database)
    finally:
        importlib.reload(importlib.import_module(__name__))


database_init()
engine = create_async_engine(DatabaseConfig.url, echo=__debug__)
sync_engine = create_engine(DatabaseConfig.sync_url, echo=__debug__)
session_maker = async_sessionmaker(bind=engine)
session = async_scoped_session(session_maker, scopefunc=current_task)
