from sqlalchemy import select, delete

from wwricu.component.database import get_session
from wwricu.domain.entity import Base, SysConfig
from wwricu.domain.enum import ConfigKeyEnum


async def insert(entity: Base) -> Base:
    async with get_session() as s:
        s.add(entity)
        await s.flush()
        await s.refresh(entity)
    return entity


async def insert_all(entities: list[Base]) -> list[Base]:
    async with get_session() as s:
        s.add_all(entities)
        await s.flush()
        for entity in entities:
            await s.refresh(entity)
    return list(entities)


async def set_config(key: ConfigKeyEnum, value: str):
    async with get_session() as s:
        await s.execute(delete(SysConfig).where(SysConfig.key == key))
        s.add(SysConfig(key=key, value=value))


async def delete_config(keys: list[ConfigKeyEnum]):
    stmt = delete(SysConfig).where(SysConfig.key.in_(keys)).where(SysConfig.deleted == False)
    async with get_session() as s:
        await s.execute(stmt)


async def get_config(key: ConfigKeyEnum) -> str | None:
    """Get config from database only, without cache"""
    stmt = select(SysConfig.value).where(SysConfig.key == key).where(SysConfig.deleted == False)
    async with get_session() as s:
        return await s.scalar(stmt)
