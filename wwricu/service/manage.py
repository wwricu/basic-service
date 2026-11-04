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
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum, EntityTypeEnum, ManageCommandEnum, TagTypeEnum, PostResourceTypeEnum
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


async def _set_about(value: str) -> None:
    await set_config(ConfigKeyEnum.ABOUT_CONTENT, value)


async def _set_username(value: str) -> None:
    if len(value) < 4 or not re.match('^[a-zA-Z][a-zA-Z0-9_]*$', value):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail='Invalid username')
    await set_config(ConfigKeyEnum.USERNAME, value)


async def _set_password(value: str) -> None:
    if len(value) < 8 or value.isalnum():
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail='Invalid password')
    credential = await asyncio.to_thread(bcrypt.hashpw, value.encode(), bcrypt.gensalt())
    await set_config(ConfigKeyEnum.PASSWORD, base64.b64encode(credential).decode())


async def _reset_login(_: str) -> None:
    await delete_config([ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD])


async def _enroll_totp(_: str) -> str:
    secret = pyotp.random_base32()
    await set_config(ConfigKeyEnum.TOTP_SECRET, secret)
    return secret


async def _confirm_totp(value: str) -> None:
    if (secret := await get_config(ConfigKeyEnum.TOTP_SECRET)) is None:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)
    if not pyotp.TOTP(secret).verify(value, valid_window=1):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=HttpErrorDetail.WRONG_TOTP)
    await set_config(ConfigKeyEnum.TOTP_ENFORCE, str(int(time.time())))


async def _disable_totp(_: str) -> None:
    await delete_config([ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET])


MANAGE_COMMANDS: dict[ManageCommandEnum, Callable[[str], Awaitable[str | None]]] = {
    ManageCommandEnum.SET_ABOUT: _set_about,
    ManageCommandEnum.SET_USERNAME: _set_username,
    ManageCommandEnum.SET_PASSWORD: _set_password,
    ManageCommandEnum.RESET_LOGIN: _reset_login,
    ManageCommandEnum.ENROLL_TOTP: _enroll_totp,
    ManageCommandEnum.CONFIRM_TOTP: _confirm_totp,
    ManageCommandEnum.DISABLE_TOTP: _disable_totp,
}
