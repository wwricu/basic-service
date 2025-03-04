from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, TEXT, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from wwricu.domain.constant import EntityConstant
from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=datetime.now())

    def to_dict(self) -> dict:
        return {key: getattr(self, key) for key in self.__table__.columns.keys()}


class BlogPost(Base):
    __tablename__ = 'wwr_blog_post'
    title: Mapped[str] = mapped_column(String(EntityConstant.USER_STRING_LEN), default='', index=True)
    cover_id: Mapped[int] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(TEXT, default='')
    preview: Mapped[str] = mapped_column(TEXT, default='')
    status: Mapped[str] = mapped_column(
        String(EntityConstant.ENUM_STRING_LEN),
        default=PostStatusEnum.DRAFT.value,
        index=True
    )
    category_id: Mapped[int] = mapped_column(Integer, nullable=True)


class PostTag(Base):
    """
    Why we have to separate Tag and Category: these two item are NOT same after all.
    They need different renderings on page, they will finally need different structure and logics one day.
    It is not wise to store they in a same table just because of their current same structure.
    """
    __tablename__ = 'wwr_post_tag'
    __table_args__ = (UniqueConstraint('name', 'type', name='uix_name_type'),)
    name: Mapped[str] = mapped_column(String(EntityConstant.USER_STRING_LEN))
    type: Mapped[str] = mapped_column(String(EntityConstant.ENUM_STRING_LEN))
    count: Mapped[int] = mapped_column(Integer, default=0)


class EntityRelation(Base):
    __tablename__ = 'wwr_entity_relation'
    src_id: Mapped[int] = mapped_column(Integer, index=True)
    dst_id: Mapped[int] = mapped_column(Integer, index=True)
    type: Mapped[RelationTypeEnum] = mapped_column(
        String(EntityConstant.ENUM_STRING_LEN),
        default=RelationTypeEnum.POST_TAG
    )


class PostResource(Base):
    __tablename__ = 'wwr_post_resource'
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(EntityConstant.USER_STRING_LEN), nullable=True)
    key: Mapped[str] = mapped_column(String(EntityConstant.LONG_STRING_LEN))
    type: Mapped[str] = mapped_column(String(EntityConstant.ENUM_STRING_LEN), nullable=True)
    url: Mapped[str] = mapped_column(TEXT, nullable=True)


class SysConfig(Base):
    __tablename__ = 'wwr_sys_config'
    key: Mapped[str] = mapped_column(String(EntityConstant.USER_STRING_LEN), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(TEXT, nullable=True)
