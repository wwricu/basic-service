import importlib
import os
from asyncio import current_task

from loguru import logger as log
from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker, create_async_engine

from wwricu.service.storage import get_object, put_object
from wwricu.config import DatabaseConfig, StorageConfig


async def open_session():
    try:
        yield
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()
        await session.remove()


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


async def database_restore():
    # TODO: rollback on any failure
    if os.path.exists(DatabaseConfig.database):
        await session.close_all()
        await engine.dispose()
        os.remove(DatabaseConfig.database)
    importlib.reload(importlib.import_module(__name__))


database_init()
engine = create_async_engine(DatabaseConfig.url, echo=__debug__)
session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
session = async_scoped_session(session_maker, scopefunc=current_task)
