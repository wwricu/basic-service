from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from service.config import Config

Base = declarative_base()
engine = create_engine(Config.DB_URL, echo=True)
session = sessionmaker(autocommit=False,
                       autoflush=False,
                       bind=engine)


def init_db():
    if not database_exists(engine.url):
        create_database(engine.url)
    Base.metadata.create_all(engine)
