from fastapi import HTTPException, status as http_status
from sqlalchemy import delete, select

from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.entity import SysConfig
from wwricu.domain.enum import ConfigKeyEnum
from wwricu.service.database import get_session


async def set_config(key: ConfigKeyEnum, value: str):
    if not isinstance(value, str):
        raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.INVALID_VALUE)
    async with get_session() as s:
        stmt = delete(SysConfig).where(SysConfig.key == key)
        await s.execute(stmt)
        s.add(SysConfig(key=key, value=value))


async def delete_config(keys: list[ConfigKeyEnum]):
    stmt = delete(SysConfig).where(SysConfig.key.in_(keys)).where(SysConfig.deleted == False)
    async with get_session() as s:
        await s.execute(stmt)


async def get_config(key: ConfigKeyEnum) -> str | None:
    stmt = select(SysConfig.value).where(SysConfig.key == key).where(SysConfig.deleted == False)
    async with get_session() as s:
        return await s.scalar(stmt)
