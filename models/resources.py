from datetime import datetime
from sqlalchemy import Integer, Column, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from . import Base


class Resource(Base):
    __tablename__ = 'resource'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), comment="title name")
    url = Column(String(255), unique=True, comment="unique url")

    created_time = Column(DateTime,
                          default=datetime.now,
                          comment="create time")

    modified_time = Column(DateTime,
                           default=datetime.now,
                           onupdate=datetime.now,
                           comment="update time")

    parent_id = Column(Integer, ForeignKey('resource.id'))
    sub_resource = relationship("resource", backref="resource")

    type = Column(String(50))
    __mapper_args__ = {
        'polymorphic_identity': 'resource',
        'polymorphic_on': type
    }


class Content(Resource):
    __tablename__ = 'content'
    id = Column(Integer, ForeignKey('resource.id'), primary_key=True)

    sub_title = Column(String(255), comment="content summary")
    status = Column(String(255), comment="content status")
    content = Column(LargeBinary, comment="content html")

    parent_id = Column(Integer, ForeignKey('resource.id'))
    sub_resource = relationship("resource", backref="resource")

    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'inherit_condition': id == Resource.id,
    }


class Folder(Resource):
    __tablename__ = 'folder'
    id = Column(Integer, ForeignKey('resource.id'), primary_key=True)

    parent_id = Column(Integer, ForeignKey('resource.id'))
    sub_resource = relationship("resource", backref="resource")

    __mapper_args__ = {
        'polymorphic_identity': 'folder',
        'inherit_condition': id == Resource.id,
    }
