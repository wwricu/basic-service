from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

import functools

from service.config import Config
from models import Base, SysUser, SysRole


def alchemy_session(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        db = DatabaseService.get_session()
        ret = method(*args, db, **kwargs)
        db.close()
        return ret
    return wrapper


class DatabaseService:
    __engine = None

    @classmethod
    def get_engine(cls):
        if not cls.__engine:
            engine = create_engine(Config.DB_URL, echo=True)
            cls.__engine = engine
        return cls.__engine

    @classmethod
    def get_session(cls):
        engine = cls.get_engine()
        db = sessionmaker(autocommit=False,
                          autoflush=False,
                          bind=engine)()
        return db

    @classmethod
    def init_db(cls):
        engine = cls.get_engine()
        if not database_exists(engine.url):
            create_database(engine.url)
        Base.metadata.create_all(engine)

        cls.insert_admin()

    @classmethod
    @alchemy_session
    def insert_admin(cls, db):
        try:
            admin_role = SysRole(name='admin',
                                 description='Admin role')
            admin = SysUser(username=Config.admin_username,
                            email=Config.admin_email,
                            password_hash=Config.admin_password_hash,
                            salt=Config.admin_password_salt)
            db.add(admin_role)
            db.add(admin)
            admin.roles.append(admin_role)

            db.commit()
        except Exception as e:
            print(e)
