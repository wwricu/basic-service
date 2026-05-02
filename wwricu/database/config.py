from sqlalchemy import select, delete

from wwricu.component.database import get_session
from wwricu.domain.entity import SysConfig
from wwricu.domain.enum import ConfigKeyEnum


async def upsert(key: ConfigKeyEnum, value: str):
    async with get_session() as s:
        await s.execute(delete(SysConfig).where(SysConfig.key == key))
        s.add(SysConfig(key=key, value=value))


async def remove(keys: list[ConfigKeyEnum]):
    stmt = delete(SysConfig).where(SysConfig.key.in_(keys)).where(SysConfig.deleted == False)
    async with get_session() as s:
        await s.execute(stmt)


async def get(key: ConfigKeyEnum) -> str | None:
    """Get config from database only, without cache"""
    stmt = select(SysConfig.value).where(SysConfig.key == key).where(SysConfig.deleted == False)
    async with get_session() as s:
        return await s.scalar(stmt)
