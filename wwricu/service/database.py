from asyncio import current_task

from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker, create_async_engine, AsyncSession

from wwricu.config import DatabaseConfig


async def database_session() -> AsyncSession:
    try:
        yield session
    finally:
        await session.commit()
        await session.remove()


# from sqlalchemy import create_engine, Engine
# from wwricu.domain.entity import Base
# sync_engine: Engine = create_engine('sqlite:///wwr.sqlite3', echo=True)
# Base.metadata.create_all(sync_engine)


engine = create_async_engine(DatabaseConfig.get_url(), echo=__debug__)
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
session = async_scoped_session(session_maker, scopefunc=current_task)