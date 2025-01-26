from sqlalchemy import create_engine, Engine

from sqlalchemy import select

from wwricu.domain.enum import TagTypeEnum, RelationTypeEnum
from wwricu.domain.entity import Base, BlogPost, EntityRelation, PostTag


def test_create_database():
    sync_engine: Engine = create_engine('sqlite:///wwr.sqlite3', echo=True)
    Base.metadata.create_all(sync_engine)


def test_join():
    tag_name = [1]
    stmt = select(BlogPost.id).join(
        EntityRelation, BlogPost.id == EntityRelation.src_id).join(
        PostTag, EntityRelation.dst_id == PostTag.id).where(
        PostTag.deleted == False).where(
        EntityRelation.deleted == False).where(
        BlogPost.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        PostTag.name.in_(tag_name)
    )
    print(stmt)
