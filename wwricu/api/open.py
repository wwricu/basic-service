import asyncio

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, desc, func

from wwricu.domain.common import HttpErrorDetail
from wwricu.domain.entity import BlogPost, PostTag, SysConfig
from wwricu.domain.enum import CacheKeyEnum, ConfigKeyEnum, PostStatusEnum
from wwricu.domain.input import PostRequestRO, TagRequestRO
from wwricu.domain.output import TagVO, PostDetailVO, PageVO, AboutPageVO
from wwricu.service.cache import cache
from wwricu.service.category import get_category_by_name
from wwricu.service.database import session
from wwricu.service.post import get_posts_preview, get_post_detail
from wwricu.service.tag import get_post_ids_by_tag_names

open_api = APIRouter(prefix='/open', tags=['Open API'])


@open_api.post('/post/all', response_model=PageVO[PostDetailVO])
async def get_all_posts(post: PostRequestRO) -> PageVO[PostDetailVO]:
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
    posts_result, count = await asyncio.gather(session.execute(post_stmt), session.scalar(count_stmt))
    all_posts = await get_posts_preview(posts_result.all())
    return PageVO(page_index=post.page_index, page_size=post.page_size, count=count, post_details=all_posts)


@open_api.get('/post/detail/{post_id}', response_model=PostDetailVO)
async def get_open_post_detail(post_id: int) -> PostDetailVO:
    stmt = select(
        BlogPost.id,
        BlogPost.title,
        BlogPost.content,
        BlogPost.cover_id,
        BlogPost.category_id,
        BlogPost.create_time,
        BlogPost.update_time).where(
        BlogPost.id == post_id).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    if (post := (await session.execute(stmt)).one()) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    return await get_post_detail(post)


@open_api.post('/tags', response_model=list[TagVO])
async def get_all_tags(get_tag: TagRequestRO) -> list[TagVO]:
    stmt = select(PostTag).where(
        PostTag.deleted == False).where(
        PostTag.type == get_tag.type).order_by(
        desc(PostTag.update_time)
    )
    if get_tag.page_index > 0 and get_tag.page_size > 0:
        stmt = stmt.limit(get_tag.page_size).offset((get_tag.page_index - 1) * get_tag.page_size)
    return [TagVO.model_validate(tag) for tag in (await session.scalars(stmt)).all()]


@open_api.get('/about', response_model=AboutPageVO)
async def about() -> AboutPageVO:
    stmt = select(SysConfig.value).where(SysConfig.key == ConfigKeyEnum.ABOUT_CONTENT).where(SysConfig.deleted == False)
    content, post, category, tag = await asyncio.gather(
        session.scalar(stmt),
        cache.get(CacheKeyEnum.POST_COUNT),
        cache.get(CacheKeyEnum.CATEGORY_COUNT),
        cache.get(CacheKeyEnum.TAG_COUNT)
    )
    return AboutPageVO(content=content, post_count=post, category_count=category, tag_count=tag)
