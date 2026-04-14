from sqlalchemy import select, update

from wwricu.component.database import get_session
from wwricu.domain.entity import EntityRelation
from wwricu.domain.enum import RelationTypeEnum


async def delete_post_tags(post_id: int):
    stmt = update(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post_id).values(
        deleted=True
    )
    async with get_session() as s:
        await s.execute(stmt)


async def get_tag_ids_by_post_id(post_id: int) -> list[int]:
    stmt = select(EntityRelation.dst_id).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post_id
    )
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())
