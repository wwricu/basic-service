from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from config import Config
from models import Base, SysUser, SysRole, Folder


class DatabaseService:
    __engine = None

    @classmethod
    def get_engine(cls):
        if not cls.__engine:
            engine = create_engine(Config.db_url, echo=False)
            cls.__engine = engine
        return cls.__engine

    @classmethod
    def get_session(cls):
        engine = cls.get_engine()
        return sessionmaker(autocommit=False,
                            autoflush=False,
                            expire_on_commit=False,
                            bind=engine)()

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
        db = DatabaseService.get_session()
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
        finally:
            db.close()

    @classmethod
    def insert_root_folder(cls):
        db = DatabaseService.get_session()
        try:
            root_folder = Folder(title='root',
                                 permission=0,
                                 url='')
            db.add(root_folder)
            db.flush()
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
            db.add(post_folder)
            db.add(draft_folder)
            db.commit()
        except Exception as e:
            print(e)
        finally:
            db.close()


def get_db():
    db = DatabaseService.get_session()
    try:
        yield db
    finally:
        db.close()
