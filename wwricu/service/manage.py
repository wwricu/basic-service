from fastapi import HTTPException, status as http_status

from wwricu.database import common
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum
from wwricu.component.cache import cache


async def set_config(key: ConfigKeyEnum, value: str):
    if not isinstance(value, str):
        raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.INVALID_VALUE)
    await common.set_config(key, value)
    await cache.delete(CacheKeyEnum.CONFIG.format(key=key))


async def delete_config(keys: list[ConfigKeyEnum]):
    await common.delete_config(keys)
    for key in keys:
        await cache.delete(CacheKeyEnum.CONFIG.format(key=key))


async def get_config(key: ConfigKeyEnum) -> str | None:
    if (value := await cache.get(CacheKeyEnum.CONFIG.format(key=key))) is not None:
        return value
    return await common.get_config(key)
