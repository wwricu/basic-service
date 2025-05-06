import contextlib
import ssl
from asyncio import current_task
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker, create_async_engine

from wwricu.config import DatabaseConfig


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


engine = create_async_engine(
    DatabaseConfig.url,
    connect_args=dict(ssl=ssl.create_default_context()),
    echo=__debug__
)
sync_engine = create_engine(
    DatabaseConfig.sync_url,
    connect_args=dict(ssl=ssl.create_default_context()),
    echo=__debug__
)
session_maker = async_sessionmaker(bind=engine)
session = async_scoped_session(session_maker, scopefunc=current_task)
