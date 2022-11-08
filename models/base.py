from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()


def init_db():
    db_url = 'mariadb+mariadbconnector://root:153226@127.0.0.1:3306/fastdb?charset=utf8'
    engine = create_engine(db_url, echo=True)
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)
