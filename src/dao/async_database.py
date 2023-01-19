from functools import wraps
from typing import Callable
from contextvars import ContextVar
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession

from config import Config
from models import Base, SysUser, SysRole, Folder


ctx_db: ContextVar[AsyncSession | None] = ContextVar('ctx_db', default=None)


class AsyncDatabase:
    __engine: AsyncEngine = None
    __session_maker: sessionmaker = None

    @classmethod
    async def get_engine(cls) -> AsyncEngine:
        if not cls.__engine:
            engine = create_async_engine(Config.db_url, echo=False)
            cls.__engine = engine
            cls.__session_maker = sessionmaker(
                engine, expire_on_commit=False, class_=AsyncSession
            )
        return cls.__engine

    @classmethod
    async def dispose_engine(cls):
        if cls.__engine:
            await cls.__engine.dispose()

    @classmethod
    async def open_session(cls) -> AsyncSession:
        async with cls.__session_maker() as session:
            ctx_db.set(session)
            yield session

    @staticmethod
    def database_session(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(*args, **kwargs):
            return method(*args, session=ctx_db.get(), **kwargs)
        return wrapper

    @classmethod
    async def init_database(cls):
        engine = await cls.get_engine()
        # TODO: create database
        # if not database_exists(engine.url):
        #     create_database(engine.url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await cls.insert_admin()
        await cls.insert_root_folder()

    @classmethod
    async def insert_admin(cls):
        # TODO: suppress warning
        session: AsyncSession = cls.__session_maker()
        try:
            admin_role = SysRole(name='admin',
                                 description='Admin role')
            admin = SysUser(username=Config.admin_username,
                            email=Config.admin_email,
                            password_hash=Config.admin_password_hash,
                            salt=Config.admin_password_salt)
            session.add(admin_role)
            session.add(admin)
            admin.roles.append(admin_role)

            await session.commit()
        except (Exception,):
            await session.rollback()
        finally:
            await session.close()

    @classmethod
    async def insert_root_folder(cls):
        session: AsyncSession = cls.__session_maker()
        try:
            root_folder = Folder(title='root',
                                 permission=0,
                                 url='')
            session.add(root_folder)
            await session.flush()
            post_folder = Folder(title='post',
                                 permission=711,
                                 url='/post',
                                 owner_id=1,
                                 parent_url=root_folder.url)
            draft_folder = Folder(title='draft',
                                  permission=700,
                                  url='/draft',
                                  owner_id=1,
                                  parent_url=root_folder.url)
            session.add(post_folder)
            session.add(draft_folder)
            await session.commit()
        except (Exception,):
            await session.rollback()
        finally:
            await session.close()
