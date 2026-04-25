import contextlib
import functools
import os
from asyncio import current_task
from typing import AsyncGenerator, cast, Callable

from anyio import open_file
from loguru import logger as log
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker, create_async_engine, AsyncEngine

from wwricu.component.storage import oss_private
from wwricu.config import app_config, DatabaseConfig


@contextlib.asynccontextmanager
async def get_session_manager() -> AsyncGenerator[AsyncSession, None]:
    current_session: AsyncSession = database_manager.scoped_session()
    if current_session.is_active and current_session.in_transaction():
        yield current_session
    else:
        try:
            async with database_manager.scoped_session.begin():
                yield database_manager.scoped_session()
        finally:
            await database_manager.scoped_session.remove()


def get_session() -> contextlib.AbstractAsyncContextManager[AsyncSession]:
    return cast(contextlib.AbstractAsyncContextManager[AsyncSession], get_session_manager())


def transaction(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with get_session():
            return await func(*args, **kwargs)
    return wrapper


class DatabaseManager:
    engine: AsyncEngine
    scoped_session: async_scoped_session

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.init()

    def init(self):
        if not os.path.exists(self.config.database) and (data := oss_private.sync_get(self.config.database)):
            log.warning(f'Download database as {self.config.database}')
            with open(self.config.database, mode='wb+') as f:
                f.write(data)
        self.engine = create_async_engine(self.config.url, echo=__debug__)
        session_maker = async_sessionmaker(bind=self.engine, expire_on_commit=False)
        self.scoped_session = async_scoped_session(session_maker, scopefunc=current_task)

    async def backup(self):
        if __debug__ or not os.path.exists(self.config.database):
            return
        log.warning(f'Backup database {self.config.database}')
        async with await open_file(self.config.database, mode='rb') as f:
            # PRICED call on each restart and every week
            await oss_private.put(self.config.database, await f.read())
        log.info('Backup database success')

    async def restore(self):
        await self.engine.dispose()
        os.remove(self.config.database)
        self.init()
        log.info('Restore database success')

    async def close(self):
        await self.engine.dispose()
        await self.backup()


database_manager = DatabaseManager(app_config.database)
