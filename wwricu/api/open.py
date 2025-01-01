from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, desc

from wwricu.domain.common import HttpErrorDetail
from wwricu.domain.entity import BlogPost, PostTag
from wwricu.domain.enum import PostStatusEnum
from wwricu.domain.input import PostRequestRO, TagRequestRO
from wwricu.domain.output import TagVO, PostDetailVO
from wwricu.service.database import session
from wwricu.service.post import get_all_post_details


open_api = APIRouter(prefix='/open', tags=['Open API'])


@open_api.post('/post/all', response_model=list[PostDetailVO])
async def get_all_posts(post: PostRequestRO) -> list[PostDetailVO]:
    stmt = select(
        BlogPost.id,
        BlogPost.preview,
        BlogPost.cover_id,
        BlogPost.category_id,
        BlogPost.create_time,
        BlogPost.update_time
    ).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED).order_by(
        desc(BlogPost.update_time)).limit(
        post.page_size).offset(
        (post.page_index - 1) * post.page_size
    )
    all_posts = (await session.scalars(stmt)).all()
    return await get_all_post_details(all_posts)


@open_api.get('/post/detail/{post_id}', response_model=PostDetailVO)
async def get_post_detail(post_id: int) -> PostDetailVO:
    stmt = select(
        BlogPost.id,
        BlogPost.content,
        BlogPost.cover_id,
        BlogPost.category_id,
        BlogPost.create_time,
        BlogPost.update_time
    ).where(
        BlogPost.id == post_id).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    if (post := await session.scalar(stmt)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    return await get_post_detail(post)


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
