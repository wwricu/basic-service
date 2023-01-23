from datetime import datetime
from types import MappingProxyType

from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, LargeBinary, String
)
from sqlalchemy.orm import relationship

from .sys_user import Base
from .tag import PostTag


class Resource(Base):
    def __init__(
            self,
            id: int | None = None,
            title: str | None = None,
            url: str | None = None,
            permission: int | None = None,
            parent_url: str | None = None,
            **kwargs
    ):
        super().__init__()
        self.id = id
        self.title = title
        self.url = url
        self.permission = permission
        self.parent_url = parent_url

    __tablename__ = 'resource'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    url = Column(String(255), unique=True)
    this_url = Column(String(255), comment='For concat after rename')

    owner_id = Column(Integer, ForeignKey('sys_user.id'))
    owner = relationship("SysUser", back_populates="resources")

    group_id = Column(
        Integer,
        ForeignKey('sys_role.id'),
        comment='Sys role as group'
    )
    group = relationship("SysRole", back_populates="resources")

    permission = Column(Integer)

    created_time = Column(
        DateTime,
        default=datetime.now,
        comment="create time"
    )

    updated_time = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="update time"
    )

    parent_url = Column(
        String(255),
        ForeignKey('resource.url'),
        nullable=True
    )
    parent = relationship(
        'Resource',
        remote_side=url,
        back_populates='sub_resource',
        uselist=False
    )
    sub_resource = relationship(
        "Resource",
        foreign_keys=parent_url,
        back_populates='parent',
        cascade="all"
    )

    type = Column(String(50))
    __mapper_args__ = {
        # 'polymorphic_identity': 'resource',
        'polymorphic_on': type
    }


class Folder(Resource):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    __tablename__ = 'folder'
    id = Column(
        Integer,
        ForeignKey('resource.id', ondelete='CASCADE'),
        primary_key=True
    )

    # parent_id = Column(Integer, ForeignKey('resource.id'))
    # sub_resource = relationship("Resource", foreign_keys=parent_id)

    __mapper_args__ = {
        'polymorphic_identity': 'folder',
        'inherit_condition': id == Resource.id,
    }


class Content(Resource):
    def __init__(
            self,
            category: dict = MappingProxyType({}),
            tags: list[dict] = (),
            content: bytes | None = None,
            **kwargs
    ):
        super().__init__(**kwargs)
        if category is not None:
            self.category_id = category.get('id')
        if tags is not None:
            self.tags = [PostTag(**tag) for tag in tags]
        self.content = content

    __tablename__ = 'content'
    id = Column(
        Integer,
        ForeignKey('resource.id', ondelete='CASCADE'),
        primary_key=True
    )

    sub_title = Column(String(255), nullable=True, comment="content summary")
    content = Column(
        LargeBinary(length=65536),
        nullable=True,
        comment="content html"
    )

    category_id = Column(Integer, ForeignKey('post_category.id'))
    category = relationship(
        "PostCategory",
        back_populates="posts",
        lazy="selectin"
    )

    tags = relationship(
        'PostTag',
        secondary='post_tag_relation',
        back_populates='posts',
        cascade="save-update",
        lazy="selectin"
    )

    __mapper_args__ = {
        'polymorphic_identity': 'content',
        'inherit_condition': id == Resource.id,
    }
