from fastapi import HTTPException, status as http_status
from sqlalchemy import delete, select

from wwricu.service.database import session
from wwricu.domain.entity import SysConfig
from wwricu.domain.enum import ConfigKeyEnum


async def set_config(key: ConfigKeyEnum, value: str):
    if isinstance(value, str):
        raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE)
    stmt = delete(SysConfig).where(SysConfig.key == key)
    await session.execute(stmt)
    session.add(SysConfig(key=key, value=value))


async def delete_config(keys: list[ConfigKeyEnum]):
    stmt = delete(SysConfig).where(SysConfig.key.in_(keys))
    await session.execute(stmt)


async def get_config(key: ConfigKeyEnum) -> str | None:
    stmt = select(SysConfig.value).where(SysConfig.key == key).where(SysConfig.deleted == False)
    return await session.scalar(stmt)
