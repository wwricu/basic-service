import functools
from contextvars import ContextVar
from typing import Callable

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
    AsyncSession
)
from sqlalchemy.orm import close_all_sessions

from config import Config, logger
from models import Base, SysUser, SysRole


ctx_db: ContextVar[AsyncSession | None] = ContextVar('ctx_db', default=None)


class AsyncDatabase:
    __engine: AsyncEngine = None
    __session_maker: async_sessionmaker = None

    @classmethod
    async def get_engine(cls) -> AsyncEngine:
        if not cls.__engine:
            engine = create_async_engine(
                URL.create(**Config.database.__dict__), echo=False
            )
            cls.__engine = engine
            cls.__session_maker = async_sessionmaker(
                engine, expire_on_commit=False
            )
        return cls.__engine

    @classmethod
    async def close(cls):
        close_all_sessions()
        if cls.__engine:
            await cls.__engine.dispose()

    @classmethod
    async def open_session(cls) -> AsyncSession:
        async with cls.__session_maker() as session:
            ctx_db.set(session)
            yield session

    @staticmethod
    def database_session(method: Callable) -> Callable:
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            return method(*args, session=ctx_db.get(), **kwargs)
        return wrapper

    @classmethod
    async def init_database(cls):
        engine = create_async_engine(
            URL.create(
                drivername=Config.database.drivername,
                username=Config.database.username,
                password=Config.database.password,
                host=Config.database.host,
                port=Config.database.port
            ),
            # CREATE DATABASE cannot in transaction
            isolation_level="AUTOCOMMIT"
        )

        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text(f"CREATE DATABASE {Config.database.database}")
                )
        except ProgrammingError:
            pass
        finally:
            await engine.dispose()

        engine = await cls.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await cls.insert_admin()
        await cls.insert_root_folder()

    @classmethod
    async def insert_admin(cls):
        session: AsyncSession = cls.__session_maker()
        try:
            admin_role = SysRole(**Config.admin.role)
            admin = SysUser(
                username=Config.admin.username,
                password_hash=Config.admin.password_hash,
                salt=Config.admin.salt,
                email=Config.admin.email
            )

            session.add(admin_role)
            session.add(admin)
            admin.roles.append(admin_role)

            await session.commit()
        except IntegrityError:
            pass
        except Exception as e:
            logger.warn(e)
            await session.rollback()
        finally:
            await session.close()

    @classmethod
    async def insert_root_folder(cls):
        session: AsyncSession = cls.__session_maker()
        try:
            for folder in Config.folders:
                session.add(folder)
            await session.commit()
        except IntegrityError:
            pass
        except Exception as e:
            logger.warn(e)
            await session.rollback()
        finally:
            await session.close()
