from typing import Sequence

from sqlalchemy import select, update

from wwricu.domain.entity import BlogPost, PostTag, EntityRelation
from wwricu.domain.enum import TagTypeEnum, RelationTypeEnum
from wwricu.service.database import session


async def get_tags_by_ids(tag_id_list: list[int] = ()) -> list[PostTag]:
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        PostTag.deleted == False).where(
        PostTag.id.in_(tag_id_list)
    )
    return list((await session.scalars(stmt)).all())


async def get_category_by_id(category_id: int) -> PostTag:
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT.value).where(
        PostTag.deleted == False).where(
        PostTag.id == category_id
    )
    return await session.scalar(stmt)


async def update_tags(post: BlogPost, tag_id_list: list[int] | None = None) -> list[PostTag]:
    if tag_id_list is None:
        return []
    tags = await get_tags_by_ids(tag_id_list)
    stmt = update(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post.id
    ).values(deleted=True)
    await session.execute(stmt)
    relations = [EntityRelation(src_id=post.id, dst_id=t.id, type=RelationTypeEnum.POST_TAG) for t in tags]
    session.add_all(relations)
    return tags


async def update_category(post: BlogPost, category_id: int | None = None) -> PostTag | None:
    if category_id is None:
        return None
    category = await get_category_by_id(category_id)
    if category is None:
        return None
    stmt = update(BlogPost).where(
        BlogPost.id == post.id).where(
        BlogPost.deleted == False
    ).values(category_id=category.id)
    await session.execute(stmt)
    return category


async def get_post_tags(post: BlogPost) -> list[PostTag]:
    stmt = select(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post.id
    )
    tag_relations = (await session.scalars(stmt)).all()
    return await get_tags_by_ids([relation.dst_id for relation in tag_relations])


async def get_post_category(post: BlogPost) -> PostTag:
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.id == post.category_id
    )
    return await session.scalar(stmt)


async def get_posts_tag_lists(post_list: Sequence[BlogPost]) -> dict[int, list[PostTag]]:
    post_tags_dict = {post.id: [] for post in post_list}
    relation_stmt = select(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id.in_(post_tags_dict.keys())
    )
    tag_relations = (await session.scalars(relation_stmt)).all()
    tag_dict = {tag.id: tag for tag in await get_tags_by_ids([relation.dst_id for relation in tag_relations])}
    for relation in tag_relations:
        post_tags = post_tags_dict.get(relation.src_id)
        tag = tag_dict.get(relation.dst_id)
        post_tags.append(tag)
    return post_tags_dict


async def get_posts_category(post_list: Sequence[BlogPost]) -> dict[int, PostTag]:
    cat_stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.id.in_([post.category_id for post in post_list])
    )
    category_dict = {cat.id: cat for cat in (await session.scalars(cat_stmt)).all()}
    return {post.id: category_dict.get(post.category_id) for post in post_list}