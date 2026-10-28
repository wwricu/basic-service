import contextlib
import functools
import os
import sqlite3
import sys
from asyncio import current_task
from typing import AsyncGenerator, cast, Callable

from loguru import logger as log
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker, create_async_engine, AsyncEngine

from wwricu.config import app_config, env


@contextlib.asynccontextmanager
async def get_session_manager() -> AsyncGenerator[AsyncSession, None]:
    current_session: AsyncSession = this.scoped_session()
    if current_session.is_active and current_session.in_transaction():
        yield current_session
    else:
        try:
            async with this.scoped_session.begin():
                yield this.scoped_session()
        finally:
            await this.scoped_session.remove()


def get_session() -> contextlib.AbstractAsyncContextManager[AsyncSession]:
    return cast(contextlib.AbstractAsyncContextManager[AsyncSession], get_session_manager())


def transaction(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with get_session():
            return await func(*args, **kwargs)
    return wrapper


async def init():
    if not os.path.exists(app_config.database.name):
        raise FileNotFoundError(f'Database file {app_config.database.name} not found')
    this.engine = create_async_engine(app_config.database.url, echo=env.is_dev)
    session_maker = async_sessionmaker(bind=this.engine, expire_on_commit=False)
    this.scoped_session = async_scoped_session(session_maker, scopefunc=current_task)


async def backup(path: str):
    if os.path.exists(path):
        raise FileExistsError(f'Backup file {path} already exists')
    log.info(f'Backup database {app_config.database.name} begin')
    with contextlib.closing(sqlite3.connect(app_config.database.name)) as source:
        source.execute('VACUUM INTO ?', (path,))
    log.info(f'Backup database {app_config.database.name} success')


async def close():
    await this.engine.dispose()


engine: AsyncEngine
scoped_session: async_scoped_session
this = sys.modules[__name__]
