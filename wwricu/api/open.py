import asyncio

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, desc

from wwricu.domain.common import HttpErrorDetail
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import PostStatusEnum
from wwricu.domain.input import PostRequestRO, TagRequestRO
from wwricu.domain.output import TagVO, PostDetailVO
from wwricu.service.database import session
from wwricu.service.tag import get_posts_tag_lists, get_posts_category, get_post_category, get_post_tags


open_api = APIRouter(prefix='/open', tags=['Open API'])


@open_api.post('/post/all', response_model=list[PostDetailVO])
async def get_all_posts(post: PostRequestRO) -> list[PostDetailVO]:
    stmt = select(BlogPost).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED).order_by(
        desc(BlogPost.create_time)).limit(
        post.page_size).offset(
        (post.page_index - 1) * post.page_size
    )
    all_posts = (await session.scalars(stmt)).all()
    post_cat_dict, post_tag_dict = await asyncio.gather(
        get_posts_category(all_posts),
        get_posts_tag_lists(all_posts)
    )
    return [PostDetailVO.of(post, post_cat_dict.get(post.id), post_tag_dict.get(post.id)) for post in all_posts]


@open_api.get('/post/detail/{post_id}', response_model=PostDetailVO)
async def get_post_detail(post_id: int) -> PostDetailVO:
    stmt = select(BlogPost).where(
        BlogPost.id == post_id).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    if (post := await session.scalar(stmt)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    category, tag_list = asyncio.gather(
        get_post_category(post),
        get_post_tags(post),
    )
    return PostDetailVO.of(post, category, tag_list)


@open_api.post('/tags')
async def get_all_tags(get_tag: TagRequestRO) -> list[TagVO]:
    stmt = select(PostTag).where(
        PostTag.deleted == False).where(
        PostTag.type == get_tag.type).order_by(
        desc(PostTag.update_time)
    )
    if get_tag.page_index > 0 and get_tag.page_size > 0:
        stmt = stmt.limit(get_tag.page_size).offset((get_tag.page_index - 1) * get_tag.page_size)
    return [TagVO.model_validate(tag) for tag in (await session.scalars(stmt)).all()]
