from sqlalchemy import select, update, func, case

from wwricu.domain.entity import BlogPost, EntityRelation, PostTag
from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum, TagTypeEnum
from wwricu.service.database import new_session, session
from wwricu.domain.input import PostUpdateRO


async def get_tags_by_ids(tag_id_list: list[int] = ()) -> list[PostTag]:
    stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        PostTag.deleted == False).where(
        PostTag.id.in_(tag_id_list)
    )
    return list((await session.scalars(stmt)).all())


async def get_post_ids_by_tag_names(tag_name: list[str]) -> list[int]:
    if not tag_name:
        return []

    stmt = select(BlogPost.id).join(
        PostTag, BlogPost.id == EntityRelation.src_id).join(
        EntityRelation, PostTag.id == EntityRelation.dst_id).where(
        PostTag.deleted == False).where(
        EntityRelation.deleted == False).where(
        BlogPost.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        PostTag.name.in_(tag_name)
    )
    return (await session.scalars(stmt)).all()


async def update_tags(post: BlogPost, post_update: PostUpdateRO):
    tags = await get_tags_by_ids(post_update.tag_id_list)

    prev_tag_ids, post_tag_ids = set(), set()
    if post.status == PostStatusEnum.PUBLISHED:
        prev_tag_ids = {tag.id for tag in await get_post_tags(post)}
    if post_update.status == PostStatusEnum.PUBLISHED:
        post_tag_ids = set(post_update.tag_id_list)
    stmt = update(PostTag).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).values(
        count=case(
            (PostTag.id.in_(prev_tag_ids - post_tag_ids), PostTag.count - 1),
            (PostTag.id.in_(post_tag_ids - prev_tag_ids), PostTag.count + 1),
            else_=PostTag.count
        )
    )
    await session.execute(stmt)

    stmt = update(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post.id
    ).values(deleted=True)
    await session.execute(stmt)

    relations = [EntityRelation(src_id=post.id, dst_id=t.id, type=RelationTypeEnum.POST_TAG) for t in tags]
    session.add_all(relations)


async def update_tag_count(post: BlogPost, increment: int = 1) -> int:
    post_tags = await get_post_tags(post)
    stmt = update(PostTag).where(PostTag.id.in_(tag.id for tag in post_tags)).values(count=PostTag.count + increment)
    result = await session.execute(stmt)
    return result.rowcount


async def get_post_tags(post: BlogPost) -> list[PostTag]:
    stmt = select(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post.id
    )
    tag_relations = (await session.scalars(stmt)).all()
    return await get_tags_by_ids([relation.dst_id for relation in tag_relations])


async def get_posts_tag_lists(post_list: list[BlogPost]) -> dict[int, list[PostTag]]:
    stmt = select(PostTag, EntityRelation.src_id).join(
        EntityRelation, PostTag.id == EntityRelation.dst_id).where(
        PostTag.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id.in_(post.id for post in post_list)
    )

    query_result = (await session.execute(stmt)).all()
    result = {post.id: [] for post in post_list}
    for post_tag, post_id in query_result:
        if (post_tag_list := result.get(post_id)) is not None:
            post_tag_list.append(post_tag)
    return result


async def reset_tag_count():
    async with new_session() as s:
        subquery = select(PostTag.id, func.count(BlogPost.id).label('post_count')).join(
            EntityRelation, PostTag.id == EntityRelation.dst_id).join(
            BlogPost, EntityRelation.src_id == BlogPost.id).where(
            PostTag.deleted == False).where(
            EntityRelation.deleted == False).where(
            BlogPost.deleted == False).where(
            PostTag.type == TagTypeEnum.POST_TAG).where(
            EntityRelation.type == RelationTypeEnum.POST_TAG).where(
            BlogPost.status == PostStatusEnum.PUBLISHED
        ).group_by(PostTag.id).subquery()
        stmt = update(PostTag).where(PostTag.id == subquery.c.id).values(count=subquery.c.post_count)
        await s.execute(stmt)
