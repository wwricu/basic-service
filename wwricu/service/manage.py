from fastapi import HTTPException, status as http_status
from sqlalchemy import delete, select

from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.entity import SysConfig
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum
from wwricu.service.cache import cache
from wwricu.service.database import get_session


async def set_config(key: ConfigKeyEnum, value: str):
    if not isinstance(value, str):
        raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.INVALID_VALUE)

    async with get_session() as s:
        stmt = delete(SysConfig).where(SysConfig.key == key)
        await s.execute(stmt)
        s.add(SysConfig(key=key, value=value))
    await cache.delete(CacheKeyEnum.CONFIG.format(key=key))


async def delete_config(keys: list[ConfigKeyEnum]):
    stmt = delete(SysConfig).where(SysConfig.key.in_(keys)).where(SysConfig.deleted == False)
    async with get_session() as s:
        await s.execute(stmt)
    for key in keys:
        await cache.delete(CacheKeyEnum.CONFIG.format(key=key))


async def get_config(key: ConfigKeyEnum) -> str | None:
    if (value := await cache.get(CacheKeyEnum.CONFIG.format(key=key))) is not None:
        return value

    stmt = select(SysConfig.value).where(SysConfig.key == key).where(SysConfig.deleted == False)
    async with get_session() as s:
        result = await s.scalar(stmt)
    await cache.set(CacheKeyEnum.CONFIG.format(key=key), result)
    return result
