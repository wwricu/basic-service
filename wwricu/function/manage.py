import base64
import datetime
import re

import bcrypt
import pyotp
from fastapi import HTTPException, status as http_status
from sqlalchemy import update, delete

from wwricu.config import Config
from wwricu.database import common
from wwricu.database.post import get_posts_by_example
from wwricu.database.tag import get_tags_by_example
from wwricu.domain.common import TrashBinRO, TrashBinVO, UserRO
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum, EntityTypeEnum, PostStatusEnum, TagTypeEnum
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.post import PostQueryDTO
from wwricu.domain.tag import TagQueryDTO
from wwricu.component.cache import cache
from wwricu.component.database import get_session


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
    if (value := await common.get_config(key)) is not None:
        await cache.set(CacheKeyEnum.CONFIG.format(key=key), value)
    return value


async def get_trash_list() -> list[TrashBinVO]:
    deadline = datetime.datetime.now() - datetime.timedelta(days=Config.trash_expire_day)

    deleted_post = [TrashBinVO(
        id=post.id,
        name=post.title,
        type=EntityTypeEnum.BLOG_POST,
        status=PostStatusEnum(post.status),
        delete_time=post.update_time
    ) for post in await get_posts_by_example(PostQueryDTO(deadline=deadline, deleted=True))]

    deleted_tag = [TrashBinVO(
        id=tag.id,
        name=tag.name,
        type=EntityTypeEnum.POST_TAG if tag.type == TagTypeEnum.POST_TAG else EntityTypeEnum.POST_CAT,
        delete_time=tag.update_time
    ) for tag in await get_tags_by_example(TagQueryDTO(deleted=True, deadline=deadline))]

    result = deleted_post + deleted_tag
    result.sort(key=lambda item: item.delete_time, reverse=True)
    return result


async def update_trash(trash_bin: TrashBinRO) -> None:
    entity: type[BlogPost] | type[PostTag] | None = None
    match trash_bin.type:
        case EntityTypeEnum.BLOG_POST:
            entity = BlogPost
        case EntityTypeEnum.POST_CAT | EntityTypeEnum.POST_TAG:
            entity = PostTag
        case _:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.UNKNOWN_ENTITY_TYPE)
    async with get_session() as s:
        stmt = delete(entity) if trash_bin.delete else update(entity).values(deleted=False)
        await s.execute(stmt.where(entity.deleted == True).where(entity.id == trash_bin.id))


async def update_user_config(user: UserRO, session_id: str | None) -> None:
    if user.username is not None:
        if len(user.username) < 4 or not bool(re.match('^[a-zA-Z][a-zA-Z0-9_-]*$', user.username)):
            raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE, detail='Invalid username')
        await set_config(ConfigKeyEnum.USERNAME, user.username)

    if user.password is not None:
        if len(user.password) < 8 or user.password.isalnum():
            raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE, detail='Invalid password')
        credential = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())
        await set_config(ConfigKeyEnum.PASSWORD, base64.b64encode(credential).decode())

    if user.reset:
        await delete_config([ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD])

    if user.username is not None or user.password is not None or user.reset is True:
        await cache.delete(session_id)


async def enforce_totp(enforce: bool) -> str | None:
    if not enforce:
        await delete_config([ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET])
        return None
    secret = pyotp.random_base32()
    await set_config(ConfigKeyEnum.TOTP_SECRET, secret)
    return secret


async def confirm_totp(totp: str) -> None:
    if (secret := await get_config(ConfigKeyEnum.TOTP_SECRET)) is None:
        raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.NO_TOTP_SECRET)
    totp_client = pyotp.TOTP(secret)
    if not totp_client.verify(totp, valid_window=1):
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_TOTP)
    await set_config(ConfigKeyEnum.TOTP_ENFORCE, str(True))
