from datetime import datetime

from sqlalchemy import String, Integer, Boolean, TEXT, DateTime, func, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from wwricu.domain.common import EntityConstant
from wwricu.domain.enum import RelationTypeEnum, PostStatusEnum


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    update_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=datetime.now())

    def to_dict(self) -> dict:
        return {key: getattr(self, key) for key in self.__table__.columns.keys()}


class BlogPost(Base):
    __tablename__ = 'wwr_blog_post'
    title: Mapped[str] = mapped_column(String(EntityConstant.USER_STRING_LEN), default='', index=True)
    cover_id: Mapped[int] = mapped_column(Integer(), nullable=True)
    content: Mapped[str] = mapped_column(TEXT(), default='')
    preview: Mapped[str] = mapped_column(TEXT(), default='')
    status: Mapped[str] = mapped_column(
        String(EntityConstant.ENUM_STRING_LEN),
        default=PostStatusEnum.DRAFT.value,
        index=True
    )
    category_id: Mapped[int] = mapped_column(Integer(), nullable=True)


class PostTag(Base):
    __tablename__ = 'wwr_post_tag'
    __table_args__ = (UniqueConstraint('name', 'type', name='uix_name_type'),)
    name: Mapped[str] = mapped_column(String(EntityConstant.USER_STRING_LEN))
    type: Mapped[str] = mapped_column(String(EntityConstant.ENUM_STRING_LEN))


class EntityRelation(Base):
    __tablename__ = 'wwr_entity_tag_relation'
    src_id: Mapped[int] = mapped_column(Integer(), index=True)
    dst_id: Mapped[int] = mapped_column(Integer(), index=True)
    type: Mapped[RelationTypeEnum] = mapped_column(
        String(EntityConstant.ENUM_STRING_LEN),
        default=RelationTypeEnum.POST_TAG
    )


class PostResource(Base):
    __tablename__ = 'wwr_post_resource'
    post_id: Mapped[int] = mapped_column(Integer(), index=True)
    name: Mapped[str] = mapped_column(
        String(EntityConstant.USER_STRING_LEN),
        nullable=True,
        comment='File original name'
    )
    key: Mapped[str] = mapped_column(String(EntityConstant.LONG_STRING_LEN), comment='OSS Key')
    type: Mapped[str] = mapped_column(String(EntityConstant.ENUM_STRING_LEN), nullable=True)
    url: Mapped[str] = mapped_column(TEXT(), nullable=True, comment='Public url')
