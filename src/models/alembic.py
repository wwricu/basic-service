from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

# This model shall NOT be merged into general Base
AlembicBase = declarative_base()


class AlembicVersion(AlembicBase):
    __tablename__ = 'alembic_version'
    ALEMBIC_VERSION: str = '69366a21b194'
    version_num = Column(String(32), primary_key=True, nullable=False)

    def __init__(self):
        self.version_num = self.ALEMBIC_VERSION
