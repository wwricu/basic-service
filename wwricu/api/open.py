import asyncio

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, desc, func

from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum, PostStatusEnum, EntityTypeEnum
from wwricu.domain.common import AboutPageVO, PageVO
from wwricu.domain.post import PostDetailVO, PostRequestRO
from wwricu.domain.tag import TagVO
from wwricu.service.cache import cache, transient
from wwricu.service.category import get_category_by_name
from wwricu.service.database import session
from wwricu.service.manage import get_config
from wwricu.service.post import get_post_detail, get_posts_preview
from wwricu.service.tag import get_post_ids_by_tag_names

open_api = APIRouter(prefix='/open', tags=['Open API'])


@open_api.post('/post/all', response_model=PageVO[PostDetailVO])
async def open_get_posts(post: PostRequestRO) -> PageVO[PostDetailVO]:
    cache_key = CacheKeyEnum.ALL_POSTS.format(
        page_index=post.page_index,
        page_size=post.page_size,
        category=post.category,
        tag_list=post.tag_list if post.tag_list else None
    )
    if response := await transient.get(cache_key):
        return response
    stmt = select(
        BlogPost.id,
        BlogPost.title,
        BlogPost.preview,
        BlogPost.cover_id,
        BlogPost.category_id,
        BlogPost.create_time,
        BlogPost.update_time).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    if category := await get_category_by_name(post.category):
        stmt = stmt.where(BlogPost.category_id == category.id)
    if post.tag_list is not None:
        post_id_list = await get_post_ids_by_tag_names(post.tag_list)
        stmt = stmt.where(BlogPost.id.in_(post_id_list))
    count_stmt = select(func.count()).select_from(stmt.subquery())
    post_stmt = stmt.order_by(
        desc(BlogPost.create_time)).limit(
        post.page_size).offset(
        (post.page_index - 1) * post.page_size
    )
    posts_result = await session.execute(post_stmt)
    count = await session.scalar(count_stmt)
    all_posts = await get_posts_preview(posts_result.all())
    response = PageVO(page_index=post.page_index, page_size=post.page_size, count=count, data=all_posts)
    await transient.set(cache_key, response)
    return response


@open_api.get('/post/detail/{post_id}', response_model=PostDetailVO)
async def open_get_post(post_id: int) -> PostDetailVO:
    cache_key = CacheKeyEnum.POST_DETAIL.format(id=post_id)
    if post := await cache.get(cache_key):
        return await get_post_detail(post)
    stmt = select(
        BlogPost.id,
        BlogPost.title,
        BlogPost.preview,
        BlogPost.content,
        BlogPost.cover_id,
        BlogPost.category_id,
        BlogPost.create_time,
        BlogPost.update_time).where(
        BlogPost.id == post_id).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    if (post := (await session.execute(stmt)).first()) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    await cache.set(cache_key, post)
    return await get_post_detail(post)


@open_api.get('/tags/{tag_type}', response_model=list[TagVO])
async def open_get_tags(tag_type: EntityTypeEnum) -> list[TagVO]:
    cache_key = CacheKeyEnum.ALL_TAGS.format(type=tag_type)
    if response := await transient.get(cache_key):
        return response

    stmt = select(PostTag).where(
        PostTag.deleted == False).where(
        PostTag.type == tag_type).order_by(
        desc(PostTag.create_time)
    )

    response = [TagVO.model_validate(tag) for tag in (await session.scalars(stmt)).all()]
    await transient.set(cache_key, response)
    return response


@open_api.get('/about', response_model=AboutPageVO)
async def open_get_about() -> AboutPageVO:
    post, category, tag = await asyncio.gather(
        cache.get(CacheKeyEnum.POST_COUNT),
        cache.get(CacheKeyEnum.CATEGORY_COUNT),
        cache.get(CacheKeyEnum.TAG_COUNT)
    )
    return AboutPageVO(
        content=await get_config(ConfigKeyEnum.ABOUT_CONTENT),
        post_count=post,
        category_count=category,
        tag_count=tag,
        startup_timestamp=await cache.get(CacheKeyEnum.STARTUP_TIMESTAMP)
    )
