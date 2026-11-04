import asyncio
import base64
import re
import time
from collections.abc import Awaitable, Callable

import bcrypt
import pyotp
from fastapi import HTTPException, status as http_status

from wwricu.component.cache import sys_cache
from wwricu.database import conf_db, post_db, tag_db, res_db
from wwricu.domain.common import TrashBinVO
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum, EntityTypeEnum, TagTypeEnum, PostResourceTypeEnum
from wwricu.domain.post import PostQueryDTO
from wwricu.domain.tag import TagQueryDTO


async def set_config(key: ConfigKeyEnum, value: str):
    await conf_db.upsert(key, value)
    await sys_cache.delete(CacheKeyEnum.CONFIG.format(key=key))


async def delete_config(keys: list[ConfigKeyEnum]):
    await conf_db.remove(keys)
    for key in keys:
        await sys_cache.delete(CacheKeyEnum.CONFIG.format(key=key))


async def get_config(key: ConfigKeyEnum) -> str | None:
    if (value := await sys_cache.get(CacheKeyEnum.CONFIG.format(key=key))) is not None:
        return value
    if (value := await conf_db.get(key)) is not None:
        await sys_cache.set(CacheKeyEnum.CONFIG.format(key=key), value)
    return value


async def list_trash() -> list[TrashBinVO]:
    deleted_post = [TrashBinVO(
        id=post.id,
        name=post.title,
        info=post.preview,
        type=EntityTypeEnum.BLOG_POST,
        delete_time=post.update_time
    ) for post in await post_db.find_by_criteria(PostQueryDTO(deleted=True))]

    deleted_tag = [TrashBinVO(
        id=tag.id,
        name=tag.name,
        type=EntityTypeEnum.POST_TAG if tag.type == TagTypeEnum.POST_TAG else EntityTypeEnum.POST_CAT,
        delete_time=tag.update_time
    ) for tag in await tag_db.find_by_criteria(TagQueryDTO(deleted=True))]

    deleted_res = [TrashBinVO(
        id=res.id,
        name=res.name,
        info=res.url,
        type=EntityTypeEnum.POST_IMAGE if res.type == PostResourceTypeEnum.IMAGE else EntityTypeEnum.POST_COVER,
        delete_time=res.update_time
    ) for res in await res_db.find_deleted()]

    result = deleted_post + deleted_tag + deleted_res
    result.sort(key=lambda item: item.delete_time, reverse=True)
    return result


async def _as_is(value: str) -> str:
    return value


async def _validated_username(username: str) -> str:
    if len(username) < 4 or not re.match('^[a-zA-Z][a-zA-Z0-9_]*$', username):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail='Invalid username')
    return username


async def _hashed_password(password: str) -> str:
    if len(password) < 8 or password.isalnum():
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail='Invalid password')
    credential = await asyncio.to_thread(bcrypt.hashpw, password.encode(), bcrypt.gensalt())
    return base64.b64encode(credential).decode()


WRITE_RULES: dict[ConfigKeyEnum, Callable[[str], Awaitable[str]]] = {
    ConfigKeyEnum.ABOUT_CONTENT: _as_is,
    ConfigKeyEnum.USERNAME: _validated_username,
    ConfigKeyEnum.PASSWORD: _hashed_password,
}

AGGREGATE: dict[ConfigKeyEnum, tuple[ConfigKeyEnum, ...]] = {
    key: group for group in (
        (ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD),
        (ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET),
    ) for key in group
}


async def write_config(key: ConfigKeyEnum, value: str | None):
    if value is None:
        await delete_config(list(AGGREGATE.get(key, (key,))))
        return
    if key not in WRITE_RULES:
        raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE)
    await set_config(key, await WRITE_RULES[key](value))


async def enroll_totp() -> str:
    secret = pyotp.random_base32()
    await set_config(ConfigKeyEnum.TOTP_SECRET, secret)
    return secret


async def confirm_totp(totp: str):
    if (secret := await get_config(ConfigKeyEnum.TOTP_SECRET)) is None:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)
    if not pyotp.TOTP(secret).verify(totp, valid_window=1):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=HttpErrorDetail.WRONG_TOTP)
    await set_config(ConfigKeyEnum.TOTP_ENFORCE, str(int(time.time())))
