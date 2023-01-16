from functools import wraps
from typing import Callable
from contextvars import ContextVar
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database

from config import Config
from models import Base, SysUser, SysRole, Folder


ctx_db: ContextVar[Session | None] = ContextVar('ctx_db', default=None)


class DatabaseService:
    __engine: Engine = None

    @classmethod
    def get_engine(cls):
        if not cls.__engine:
            engine = create_engine(Config.db_url, echo=False)
            cls.__engine = engine
        return cls.__engine

    @classmethod
    def create_session(cls) -> Session:
        engine = cls.get_engine()
        return sessionmaker(autocommit=False,
                            autoflush=False,
                            expire_on_commit=False,
                            bind=engine)()

    @classmethod
    async def open_session(cls) -> Session:
        with cls.create_session() as session:
            '''
            This dependency must be async
            to share the same coroutine and
            context with other function.
            '''
            ctx_db.set(session)
            yield session

    @staticmethod
    def database_session(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(*args, **kwargs):
            return method(*args, session=ctx_db.get(), **kwargs)
        return wrapper

    @classmethod
    def init_db(cls):
        engine = cls.get_engine()
        if not database_exists(engine.url):
            create_database(engine.url)
        Base.metadata.create_all(engine)

        cls.insert_admin()
        cls.insert_root_folder()

    @classmethod
    def insert_admin(cls):
        session = cls.create_session()
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

            session.commit()
        except (Exception,):
            session.rollback()
        finally:
            session.close()

    @classmethod
    def insert_root_folder(cls):
        session = cls.create_session()
        try:
            root_folder = Folder(title='root',
                                 permission=0,
                                 url='')
            session.add(root_folder)
            session.flush()
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
            session.commit()
        except (Exception,):
            session.rollback()
        finally:
            session.close()
