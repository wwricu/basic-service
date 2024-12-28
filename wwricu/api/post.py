import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select, update, desc

from wwricu.domain.common import HttpErrorDetail
from wwricu.domain.entity import BlogPost, EntityRelation
from wwricu.domain.enum import PostStatusEnum
from wwricu.domain.input import PostCreateRO, PostUpdateRO, BatchIdRO, PostRequestRO
from wwricu.domain.output import PostDetailVO
from wwricu.domain.context import admin_only
from wwricu.service.database import session
from wwricu.service.post import get_post_by_id
from wwricu.service.tag import (
    update_category,
    update_tags,
    get_posts_category,
    get_posts_tag_lists,
    get_post_category,
    get_post_tags
)


post_api = APIRouter(prefix='/post', tags=['Post Management'], dependencies=[Depends(admin_only)])


@post_api.post('/create', response_model=PostDetailVO)
async def create_post(post_create: PostCreateRO) -> PostDetailVO:
    blog_post = BlogPost(
        title=post_create.title,
        cover=post_create.cover,
        content=post_create.content,
        status=PostStatusEnum.DRAFT
    )
    session.add(blog_post)
    await session.flush()
    category, tag_list = await asyncio.gather(
        update_category(blog_post, post_create.category_id),
        update_tags(blog_post, post_create.tag_id_list)
    )
    return PostDetailVO.of(blog_post, category, tag_list)


@post_api.post('/all', response_model=list[PostDetailVO])
async def select_post(post: PostRequestRO) -> list[PostDetailVO]:
    stmt = select(BlogPost).where(
        BlogPost.deleted == False).order_by(
        desc(BlogPost.create_time)).limit(
        post.page_size).offset(
        (post.page_index - 1) * post.page_size
    )
    if post.status is not None:
        stmt = stmt.where(BlogPost.status == post.status.value)
    if post.deleted is not None:
        stmt = stmt.where(BlogPost.deleted == post.deleted)
    all_posts = (await session.scalars(stmt)).all()
    post_cat_dict, post_tag_dict = await asyncio.gather(
        get_posts_category(all_posts),
        get_posts_tag_lists(all_posts)
    )
    return [PostDetailVO.of(post, post_cat_dict.get(post.id), post_tag_dict.get(post.id)) for post in all_posts]


@post_api.get('/detail/{post_id}', response_model=PostDetailVO | None)
async def get_post_detail(post_id: int) -> PostDetailVO | None:
    if (post := await get_post_by_id(post_id)) is None:
        return None
    category, tag_list = await asyncio.gather(
        get_post_category(post),
        get_post_tags(post),
    )
    return PostDetailVO.of(post, category, tag_list)


@post_api.post('/update', response_model=PostDetailVO)
async def update_post(post_update: PostUpdateRO) -> PostDetailVO:
    if (blog_post := await get_post_by_id(post_update.id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    stmt = update(BlogPost).where(BlogPost.id == post_update.id).values(
        title=post_update.title,
        cover=post_update.cover,
        content=post_update.content,
        status=post_update.status,
        category_id=post_update.category_id
    )
    await session.execute(stmt)
    category = await update_category(blog_post, post_update.category_id)
    tag_list = await update_tags(blog_post, post_update.tag_id_list)
    return PostDetailVO.of(blog_post, category, tag_list)


@post_api.post('/patch', response_model=PostDetailVO)
async def patch_post(post_update: PostUpdateRO) -> PostDetailVO:
    if (blog_post := await get_post_by_id(post_update.id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    kwargs = post_update.model_dump()
    kwargs = {k: v for k, v in kwargs.items() if k in BlogPost.__table__.c and v is not None}
    stmt = update(BlogPost).where(BlogPost.id == post_update.id).values(**kwargs)
    await session.execute(stmt)
    category = await update_category(blog_post, post_update.category_id)
    tag_list = await update_tags(blog_post, post_update.tag_id_list)
    return PostDetailVO.of(blog_post, category, tag_list)


@post_api.post('/delete', response_model=int)
async def delete_post(batch: BatchIdRO):
    stmt = update(BlogPost).where(BlogPost.id.in_(batch.id_list)).values(deleted=True)
    tag_stmt = update(EntityRelation).where(EntityRelation.src_id.in_(batch.id_list)).values(deleted=True)
    result = await session.execute(stmt)
    await session.execute(tag_stmt)
    return result.rowcount
