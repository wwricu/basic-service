from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, TEXT, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum


class Base(DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=datetime.now())

    def to_dict(self) -> dict:
        return {key: getattr(self, key) for key in self.__table__.columns.keys()}


class BlogPost(Base):
    __tablename__ = 'wwr_blog_post'
    title: Mapped[str] = mapped_column(String, default='', index=True)
    cover_id: Mapped[int] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(TEXT, default='')
    preview: Mapped[str] = mapped_column(TEXT, default='')
    status: Mapped[str] = mapped_column(String, default=PostStatusEnum.DRAFT.value, index=True)
    category_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)


class PostTag(Base):
    __tablename__ = 'wwr_post_tag'

    name: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)


class EntityRelation(Base):
    __tablename__ = 'wwr_entity_relation'

    '''
    DO NOT use composite index here cause there is fixed ordinality for src_id and dst_id,
    refer to wwricu.service.common.clean_post_resource where select with dst_id and type only;
    while wwricu.service.common.hard_delete_expiration where select with src_id and type only
    '''
    src_id: Mapped[int] = mapped_column(Integer, index=True)
    dst_id: Mapped[int] = mapped_column(Integer, index=True)
    type: Mapped[RelationTypeEnum] = mapped_column(String, index=True)


class PostResource(Base):
    __tablename__ = 'wwr_post_resource'
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    key: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String, nullable=True, index=True)
    url: Mapped[str] = mapped_column(TEXT, nullable=True)


class SysConfig(Base):
    __tablename__ = 'wwr_sys_config'
    key: Mapped[str] = mapped_column(String, unique=True)
    value: Mapped[str] = mapped_column(TEXT, nullable=True)
