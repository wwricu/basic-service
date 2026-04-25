import asyncio

from fastapi import APIRouter, HTTPException, status

from wwricu.database.post import get_public_post
from wwricu.database.tag import get_tags_by_example
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum, TagTypeEnum
from wwricu.domain.common import AboutPageVO, PageVO
from wwricu.domain.post import PostDetailVO, PostRequestRO
from wwricu.domain.tag import TagVO, TagQueryDTO
from wwricu.component.cache import cache, transient
from wwricu.service.manage import get_sys_config
from wwricu.service.post import build_post_query, get_post_detail, get_posts_by_query

open_api = APIRouter(prefix='/open', tags=['Open API'])


@open_api.post('/post/all', response_model=PageVO[PostDetailVO])
async def open_get_posts_api(post: PostRequestRO) -> PageVO[PostDetailVO]:
    cache_key = CacheKeyEnum.ALL_POSTS.format(
        page_index=post.page_index,
        page_size=post.page_size,
        category=post.category,
        tag_list=post.tag_list if post.tag_list else None
    )
    if response := await transient.get(cache_key):
        return response
    query = await build_post_query(post, public=True)
    response = await get_posts_by_query(query)
    await transient.set(cache_key, response)
    return response


@open_api.get('/post/detail/{post_id}', response_model=PostDetailVO)
async def open_get_post_api(post_id: int) -> PostDetailVO:
    cache_key = CacheKeyEnum.POST_DETAIL.format(id=post_id)
    if cached_post := await cache.get(cache_key):
        return await get_post_detail(cached_post)
    if (post := await get_public_post(post_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    await cache.set(cache_key, post)
    return await get_post_detail(post)


@open_api.get('/tags/{tag_type}', response_model=list[TagVO])
async def open_get_tags_api(tag_type: TagTypeEnum) -> list[TagVO]:
    cache_key = CacheKeyEnum.ALL_TAGS.format(type=tag_type)
    if response := await transient.get(cache_key):
        return response
    response = [TagVO.model_validate(tag) for tag in await get_tags_by_example(TagQueryDTO(type=tag_type))]
    await transient.set(cache_key, response)
    return response


@open_api.get('/about', response_model=AboutPageVO)
async def open_get_about_api() -> AboutPageVO:
    post, category, tag = await asyncio.gather(
        cache.get(CacheKeyEnum.POST_COUNT),
        cache.get(CacheKeyEnum.CATEGORY_COUNT),
        cache.get(CacheKeyEnum.TAG_COUNT)
    )
    return AboutPageVO(
        content=await get_sys_config(ConfigKeyEnum.ABOUT_CONTENT),
        post_count=post,
        category_count=category,
        tag_count=tag,
        startup_timestamp=await cache.get(CacheKeyEnum.STARTUP_TIMESTAMP)
    )
