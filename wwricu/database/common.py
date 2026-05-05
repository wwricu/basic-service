from collections.abc import Sequence

from sqlalchemy import delete, update

from wwricu.component.database import get_session
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


async def hard_delete(table: type[Base], primary_id: int):
    stmt = delete(table).where(table.id == primary_id).where(table.deleted == True)
    async with get_session() as s:
        await s.execute(stmt)


async def recover(table: type[Base], primary_id: int):
    stmt = update(table).where(table.id == primary_id).where(table.deleted == True).values(deleted=False)
    async with get_session() as s:
        await s.execute(stmt)
