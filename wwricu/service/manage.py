import base64
import re

import bcrypt
import pyotp
from fastapi import HTTPException, status as http_status

from wwricu.component.cache import sys_cache
from wwricu.component.database import transaction
from wwricu.database import common_db, conf_db, post_db, tag_db, res_db
from wwricu.domain.common import TrashBinRO, TrashBinVO, UserRO
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum, EntityTypeEnum, TagTypeEnum, PostResourceTypeEnum
from wwricu.domain.entity import BlogPost, PostTag, PostResource
from wwricu.domain.post import PostQueryDTO
from wwricu.domain.tag import TagQueryDTO
from wwricu.service.post import update_deleted


async def set_config(key: ConfigKeyEnum, value: str):
    if not isinstance(value, str):
        raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.INVALID_VALUE)
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
async def process_trash(trash_bin: TrashBinRO):
    entity = {
        EntityTypeEnum.BLOG_POST: BlogPost,
        EntityTypeEnum.POST_TAG: PostTag,
        EntityTypeEnum.POST_CAT: PostTag,
        EntityTypeEnum.POST_COVER: PostResource,
        EntityTypeEnum.POST_IMAGE: PostResource
    }.get(trash_bin.type)
    if entity is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.UNKNOWN_ENTITY_TYPE)

    if trash_bin.type == EntityTypeEnum.BLOG_POST:
        if trash_bin.delete:
            resources = await res_db.find_by_post_id(trash_bin.id)
            await res_db.delete_by_keys([res.key for res in resources])
        else:
            await update_deleted(trash_bin.id, deleted=False)
    await common_db.entity_trash(entity, trash_bin.id, hard_delete=trash_bin.delete)


async def update_admin_user(user: UserRO, session_id: str | None):
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
        await sys_cache.delete(session_id)


async def enforce_totp(enforce: bool) -> str | None:
    if not enforce:
        await delete_config([ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET])
        return None
    secret = pyotp.random_base32()
    await set_config(ConfigKeyEnum.TOTP_SECRET, secret)
    return secret


async def confirm_totp(totp: str):
    if (secret := await get_config(ConfigKeyEnum.TOTP_SECRET)) is None:
        raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.NO_TOTP_SECRET)
    totp_client = pyotp.TOTP(secret)
    if not totp_client.verify(totp, valid_window=1):
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail=HttpErrorDetail.WRONG_TOTP)
    await set_config(ConfigKeyEnum.TOTP_ENFORCE, str(True))
