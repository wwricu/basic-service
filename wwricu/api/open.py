import asyncio

from fastapi import APIRouter, HTTPException, status

from wwricu.database import post_db, tag_db
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum, TagTypeEnum
from wwricu.domain.common import AboutPageVO, PageVO
from wwricu.domain.post import PostDetailVO, PostRequestRO
from wwricu.domain.tag import TagVO, TagQueryDTO
from wwricu.component.cache import sys_cache, query_cache, post_cache
from wwricu.service import manage_service, post_service

open_api = APIRouter(prefix='/open', tags=['Open API'])


@open_api.post('/post/all', response_model=PageVO[PostDetailVO])
async def open_get_posts_api(post: PostRequestRO) -> PageVO[PostDetailVO]:
    cache_key = CacheKeyEnum.ALL_POSTS.format(
        page_index=post.page_index,
        page_size=post.page_size,
        category=post.category,
        tag_list=post.tag_list if post.tag_list else None
    )
    if response := await query_cache.get(cache_key):
        return response
    query = await post_service.build_query(post, public=True)
    response = await post_service.list_by_query(query)
    await query_cache.set(cache_key, response)
    return response


@open_api.get('/post/detail/{post_id}', response_model=PostDetailVO)
async def open_get_post_api(post_id: int) -> PostDetailVO:
    cache_key = CacheKeyEnum.POST_DETAIL.format(id=post_id)
    if cached_post := await post_cache.get(cache_key):
        return await post_service.get_detail(cached_post)
    if (post := await post_db.find_published(post_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    await post_cache.set(cache_key, post)
    return await post_service.get_detail(post)


@open_api.get('/tags/{tag_type}', response_model=list[TagVO])
async def open_get_tags_api(tag_type: TagTypeEnum) -> list[TagVO]:
    cache_key = CacheKeyEnum.ALL_TAGS.format(type=tag_type)
    if response := await query_cache.get(cache_key):
        return response
    response = [TagVO.model_validate(tag) for tag in await tag_db.get_by_criteria(TagQueryDTO(type=tag_type))]
    await query_cache.set(cache_key, response)
    return response


@open_api.get('/about', response_model=AboutPageVO)
async def open_get_about_api() -> AboutPageVO:
    post, category, tag = await asyncio.gather(
        sys_cache.get(CacheKeyEnum.POST_COUNT),
        sys_cache.get(CacheKeyEnum.CATEGORY_COUNT),
        sys_cache.get(CacheKeyEnum.TAG_COUNT)
    )
    return AboutPageVO(
        content=await manage_service.get_config(ConfigKeyEnum.ABOUT_CONTENT),
        post_count=post,
        category_count=category,
        tag_count=tag,
        startup_timestamp=await sys_cache.get(CacheKeyEnum.STARTUP_TIMESTAMP)
    )
