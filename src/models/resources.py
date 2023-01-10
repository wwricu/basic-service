from datetime import datetime
from sqlalchemy import Integer, Column, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from .sys_user import Base
from .tag import PostTag


class Resource(Base):
    __tablename__ = 'resource'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    url = Column(String(255), unique=True)
    this_url = Column(String(255), comment='For concat after rename')

    owner_id = Column(Integer, ForeignKey('sys_user.id'))
    owner = relationship("SysUser", back_populates="resources")

    group_id = Column(Integer,
                      ForeignKey('sys_role.id'),
                      comment='Sys role as group')
    group = relationship("SysRole", back_populates="resources")

    permission = Column(Integer)

    created_time = Column(DateTime,
                          default=datetime.now,
                          comment="create time")

    updated_time = Column(DateTime,
                          default=datetime.now,
                          onupdate=datetime.now,
                          comment="update time")

    parent_url = Column(String(255),
                        ForeignKey('resource.url'),
                        nullable=True)
    parent = relationship('Resource',
                          remote_side=[url],
                          back_populates='sub_resource',
                          uselist=False)
    sub_resource = relationship("Resource",
                                foreign_keys=parent_url,
                                back_populates='parent',
                                cascade="all")

    type = Column(String(50))
    __mapper_args__ = {
        # 'polymorphic_identity': 'resource',
        'polymorphic_on': type
    }


class Folder(Resource):
    @classmethod
    def init(cls, folder_input):
        return Folder(id=folder_input.id,
                      title=folder_input.title,
                      parent_url=folder_input.parent_url,
                      permission=folder_input.permission)

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
    def init(cls, content_input):
        return Content(id=content_input.id,
                       title=content_input.title,
                       parent_url=content_input.parent_url,
                       permission=content_input.permission,
                       category_id=content_input.category.id
                       if content_input.category is not None else None,
                       tags=[PostTag(id=tag.id,
                                     name=tag.name)
                             for tag in content_input.tags],
                       content=content_input.content)

    __tablename__ = 'content'
    id = Column(Integer,
                ForeignKey('resource.id', ondelete='CASCADE'),
                primary_key=True)

    sub_title = Column(String(255), nullable=True, comment="content summary")
    content = Column(LargeBinary(length=65536), nullable=True, comment="content html")

    category_id = Column(Integer, ForeignKey('post_category.id'))
    category = relationship("PostCategory", back_populates="posts")

    tags = relationship('PostTag',
                        secondary='post_tag_relation',
                        back_populates='posts',
                        cascade="save-update",
                        lazy="joined")

    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'inherit_condition': id == Resource.id,
    }
