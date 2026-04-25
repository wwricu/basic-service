import contextlib
import functools
import importlib
import os
from asyncio import current_task
from typing import AsyncGenerator, cast, Callable

from anyio import open_file
from loguru import logger as log
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker, create_async_engine

from wwricu.config import DatabaseConfig
from wwricu.component.storage import oss_private


@contextlib.asynccontextmanager
async def get_session_manager() -> AsyncGenerator[AsyncSession, None]:
    scoped_session: AsyncSession = session.registry.registry.get(current_task())
    if scoped_session is not None and scoped_session.is_active and scoped_session.in_transaction():
        yield scoped_session
    else:
        async with AsyncSession(engine, expire_on_commit=False) as s, s.begin():
            yield s


def get_session() -> contextlib.AbstractAsyncContextManager[AsyncSession]:
    return cast(contextlib.AbstractAsyncContextManager[AsyncSession], get_session_manager())


def transaction(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with get_session():
            return await func(*args, **kwargs)
    return wrapper


def database_init():
    if os.path.exists(DatabaseConfig.database):
        return
    # PRICED call on each deploy
    if database := oss_private.sync_get(DatabaseConfig.database):
        log.warning(f'Download database as {DatabaseConfig.database}')
        with open(DatabaseConfig.database, mode='wb+') as f:
            f.write(database)


async def database_backup():
    if not os.path.exists(DatabaseConfig.database):
        return
    log.warning(f'Backup database {DatabaseConfig.database}')
    async with await open_file(DatabaseConfig.database, mode='rb') as f:
        # PRICED call on each restart and every week
        await oss_private.put(DatabaseConfig.database, await f.read())
    log.info('Backup database success')


async def database_restore():
    try:
        await engine.dispose()
        os.remove(DatabaseConfig.database)
    except Exception as e:
        log.warning(f'Failed to restore database {e}')
    finally:
        importlib.reload(importlib.import_module(__name__))


database_init()
engine = create_async_engine(DatabaseConfig.url, echo=__debug__)
# expire_on_commit=False keeps entities usable after session closes
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
session = async_scoped_session(session_maker, scopefunc=current_task)
