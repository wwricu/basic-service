import asyncio
import base64
import re
import time
from collections.abc import Awaitable, Callable

import bcrypt
import pyotp
from fastapi import HTTPException, status as http_status
from pydantic import ValidationError

from wwricu.component.cache import sys_cache
from wwricu.component.database import transaction
from wwricu.database import conf_db, post_db, tag_db, res_db
from wwricu.domain.common import LoginRO, TrashBinVO
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum, EntityTypeEnum, ManageCommandEnum, ManageReadEnum, TagTypeEnum, PostResourceTypeEnum
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


@transaction
async def set_login(value: str) -> None:
    try:
        login = LoginRO.model_validate_json(value)
    except ValidationError:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)
    if len(login.username) < 4 or not re.match('^[a-zA-Z][a-zA-Z0-9_]*$', login.username):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail='Invalid username')
    if len(login.password) < 8 or login.password.isalnum():
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail='Invalid password')
    credential = await asyncio.to_thread(bcrypt.hashpw, login.password.encode(), bcrypt.gensalt())
    await set_config(ConfigKeyEnum.USERNAME, login.username)
    await set_config(ConfigKeyEnum.PASSWORD, base64.b64encode(credential).decode())


async def enroll_totp(_: str) -> str:
    secret = pyotp.random_base32()
    await set_config(ConfigKeyEnum.TOTP_SECRET, secret)
    return secret


async def confirm_totp(value: str) -> None:
    if (secret := await get_config(ConfigKeyEnum.TOTP_SECRET)) is None:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)
    if not pyotp.TOTP(secret).verify(value, valid_window=1):
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=HttpErrorDetail.WRONG_TOTP)
    await set_config(ConfigKeyEnum.TOTP_ENFORCE, str(int(time.time())))


async def write(cmd: ManageCommandEnum, value: str):
    return await write_commands[cmd](value)


async def read(cmd: ManageReadEnum):
    return await read_commands[cmd]()


write_commands: dict[ManageCommandEnum, Callable[[str], Awaitable[str | None]]] = {
    ManageCommandEnum.SET_ABOUT: lambda value: set_config(ConfigKeyEnum.ABOUT_CONTENT, value),
    ManageCommandEnum.SET_SITE_TITLE: lambda value: set_config(ConfigKeyEnum.SITE_TITLE, value),
    ManageCommandEnum.SET_SITE_TAGLINE: lambda value: set_config(ConfigKeyEnum.SITE_TAGLINE, value),
    ManageCommandEnum.SET_LOGIN: set_login,
    ManageCommandEnum.RESET_LOGIN: lambda value: delete_config([ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD]),
    ManageCommandEnum.ENROLL_TOTP: enroll_totp,
    ManageCommandEnum.CONFIRM_TOTP: confirm_totp,
    ManageCommandEnum.DISABLE_TOTP: lambda value: delete_config([ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET])
}


read_commands: dict[ManageReadEnum, Callable[[], Awaitable[str | None]]] = {
    ManageReadEnum.ABOUT: lambda: get_config(ConfigKeyEnum.ABOUT_CONTENT),
    ManageReadEnum.SITE_TITLE: lambda: get_config(ConfigKeyEnum.SITE_TITLE),
    ManageReadEnum.SITE_TAGLINE: lambda: get_config(ConfigKeyEnum.SITE_TAGLINE),
    ManageReadEnum.USERNAME: lambda: get_config(ConfigKeyEnum.USERNAME),
    ManageReadEnum.TOTP_ENFORCED: lambda: get_config(ConfigKeyEnum.TOTP_ENFORCE)
}
