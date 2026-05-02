from collections.abc import Sequence

from sqlalchemy import delete, update

from wwricu.component.database import get_session
from wwricu.database import post as post_db, resource as res_db, tag as tag_db, config as conf_db
from wwricu.domain.entity import Base


async def insert(entity: Base) -> Base:
    async with get_session() as s:
        s.add(entity)
        await s.flush()
        await s.refresh(entity)
    return entity


async def insert_all(entities: Sequence[Base]) -> list[Base]:
    async with get_session() as s:
        s.add_all(entities)
        await s.flush()
        for entity in entities:
            await s.refresh(entity)
    return list(entities)


async def entity_trash(entity: type[Base], entity_id: int, hard_delete: bool | None = False):
    async with get_session() as s:
        stmt = delete(entity) if hard_delete else update(entity).values(deleted=False)
        stmt = stmt.where(entity.id == entity_id).where(entity.deleted == True)
        await s.execute(stmt)


__all__ = ['conf_db', 'post_db', 'res_db', 'tag_db', 'insert', 'insert_all', 'entity_trash']
