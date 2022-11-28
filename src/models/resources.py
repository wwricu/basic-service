from datetime import datetime
from sqlalchemy import Integer, Column, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from . import Base


class Resource(Base):
    __tablename__ = 'resource'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), comment="title name")
    url = Column(String(255), unique=True, comment="unique url")

    owner_id = Column(Integer, ForeignKey('sys_user.id'))
    owner = relationship("SysUser", back_populates="resources")

    group_id = Column(Integer, ForeignKey('sys_role.id'))
    group = relationship("SysRole", back_populates="resources")

    permission = Column(Integer)

    created_time = Column(DateTime,
                          default=datetime.now,
                          comment="create time")

    updated_time = Column(DateTime,
                          default=datetime.now,
                          onupdate=datetime.now,
                          comment="update time")

    parent_id = Column(Integer, ForeignKey('resource.id'), nullable=True)
    parent = relationship('Resource',
                          remote_side=[id],
                          back_populates='sub_resource',
                          uselist=False)
    sub_resource = relationship("Resource",
                                foreign_keys=parent_id,
                                back_populates='parent')

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
                       tags=[Tag.init(tag) for tag in content.tags],
                       content=content.content)

    __tablename__ = 'content'
    id = Column(Integer,
                ForeignKey('resource.id', ondelete='CASCADE'),
                primary_key=True)

    sub_title = Column(String(255), nullable=True, comment="content summary")
    status = Column(String(255), nullable=True, comment="content status")
    content = Column(LargeBinary(length=65536), nullable=True, comment="content html")

    tags = relationship('Tag',
                        secondary='content_tag',
                        back_populates='contents',
                        cascade="save-update",
                        lazy="joined")

    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'inherit_condition': id == Resource.id,
    }


class Tag(Base):
    @classmethod
    def init(cls, tag_schema):
        if tag_schema is None:
            return None
        return Tag(id=tag_schema.id,
                   name=tag_schema.name)

    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True)
    contents = relationship('Content',
                            secondary='content_tag',
                            back_populates='tags')
