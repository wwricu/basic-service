from collections.abc import Sequence

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
