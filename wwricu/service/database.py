from asyncio import current_task
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker, create_async_engine, AsyncSession

from wwricu.config import DatabaseConfig


async def database_session() -> AsyncSession:
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


def sync_create_database():
    from sqlalchemy import create_engine, Engine
    from wwricu.domain.entity import Base
    sync_engine: Engine = create_engine(f'sqlite:///{DatabaseConfig.database}', echo=True)
    Base.metadata.create_all(sync_engine)


# sync_create_database()
engine = create_async_engine(DatabaseConfig.get_url(), echo=__debug__)
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
session = async_scoped_session(session_maker, scopefunc=current_task)
