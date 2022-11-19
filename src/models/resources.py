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

    parent_id = Column(Integer, ForeignKey('resource.id'), nullable=True)
    sub_resource = relationship("Resource", foreign_keys=parent_id)

    type = Column(String(50))
    __mapper_args__ = {
        # 'polymorphic_identity': 'resource',
        'polymorphic_on': type
    }


class Folder(Resource):
    @classmethod
    def init(cls, folder):
        return Folder(id=folder.id,
                      title=folder.title,
                      parent_id=folder.parent_id)

    __tablename__ = 'folder'
    id = Column(Integer,
                ForeignKey('resource.id', ondelete='CASCADE'),
                primary_key=True)

    # parent_id = Column(Integer, ForeignKey('resource.id'))
    # sub_resource = relationship("Resource", foreign_keys=parent_id)

    __mapper_args__ = {
        'polymorphic_identity': 'folder',
        'inherit_condition': id == Resource.id,
    }


class Content(Resource):
    @classmethod
    def init(cls, content):
        return Content(id=content.id,
                       title=content.title,
                       parent_id=content.parent_id,
                       sub_title=content.sub_title,
                       status=content.status,
                       content=content.content)

    __tablename__ = 'content'
    id = Column(Integer,
                ForeignKey('resource.id', ondelete='CASCADE'),
                primary_key=True)

    sub_title = Column(String(255), nullable=True, comment="content summary")
    status = Column(String(255), nullable=True, comment="content status")
    content = Column(LargeBinary, nullable=True, comment="content html")

    author_id = Column(Integer, ForeignKey('sys_user.id'))
    author = relationship("SysUser", back_populates="contents")

    tags = relationship('Tag',
                        secondary='content_tag',
                        back_populates='contents',
                        lazy="joined")

    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'inherit_condition': id == Resource.id,
    }


class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True)
    contents = relationship('Content',
                            secondary='content_tag',
                            back_populates='tags')
