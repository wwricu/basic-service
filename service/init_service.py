from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from core.config import Config
from models import Base, SysUser, SysRole


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
    def insert_admin(cls):
        try:
            db = DatabaseService.get_session()

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