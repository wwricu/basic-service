from functools import wraps
from typing import Callable
from contextvars import ContextVar
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from config import Config
from models import Base, SysUser, SysRole, Folder


ctx_db: ContextVar[AsyncSession | None] = ContextVar('ctx_db', default=None)


class AsyncDatabase:
    __engine = None
    __async_session = None

    @classmethod
    async def get_engine(cls):
        if not cls.__engine:
            engine = create_async_engine(Config.db_url, echo=False)
            cls.__engine = engine
        return cls.__engine

    @classmethod
    async def create_session(cls):
        return sessionmaker(await cls.get_engine(),
                            expire_on_commit=False,
                            class_=AsyncSession)()

    @classmethod
    async def open_session(cls) -> AsyncSession:
        maker = sessionmaker(await cls.get_engine(),
                             expire_on_commit=False,
                             class_=AsyncSession)
        async with maker() as session:
            # async with session.begin():
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
        # if not database_exists(engine.url):
        #     create_database(engine.url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await cls.insert_admin()
        await cls.insert_root_folder()

    @classmethod
    async def insert_admin(cls):
        session = await cls.create_session()
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
        session = await cls.create_session()
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
