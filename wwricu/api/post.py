import asyncio
import io
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, status, UploadFile

from sqlalchemy import select, update, desc

from wwricu.domain.common import HttpErrorDetail
from wwricu.domain.entity import BlogPost, EntityRelation, PostResource
from wwricu.domain.enum import PostStatusEnum, PostResourceTypeEnum
from wwricu.domain.input import PostUpdateRO, BatchIdRO, PostRequestRO
from wwricu.domain.output import PostDetailVO, FileUploadVO
from wwricu.service.common import admin_only
from wwricu.service.database import session
from wwricu.service.post import get_post_by_id, delete_post_cover, get_post_cover
from wwricu.service.storage import storage_put
from wwricu.service.tag import (
    update_category,
    update_tags,
    get_posts_category,
    get_posts_tag_lists,
    get_post_category,
    get_post_tags
)


post_api = APIRouter(prefix='/post', tags=['Post Management'], dependencies=[Depends(admin_only)])


@post_api.get('/create', response_model=PostDetailVO)
async def create_post() -> PostDetailVO:
    blog_post = BlogPost(status=PostStatusEnum.DRAFT)
    session.add(blog_post)
    await session.flush()
    return PostDetailVO.of(blog_post)


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
    category, tag_list, cover = await asyncio.gather(
        get_post_category(post),
        get_post_tags(post),
        get_post_cover(post)
    )
    return PostDetailVO.of(post, category, tag_list, cover)


@post_api.post('/update', response_model=PostDetailVO)
async def update_post(post_update: PostUpdateRO) -> PostDetailVO:
    if (blog_post := await get_post_by_id(post_update.id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    if blog_post.cover_id is not None and blog_post.cover_id != post_update.cover_id:
        await delete_post_cover(blog_post)
    stmt = update(BlogPost).where(BlogPost.id == post_update.id).values(
        title=post_update.title,
        content=post_update.content,
        cover_id=post_update.cover_id,
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


@post_api.post('/upload', response_model=FileUploadVO)
async def upload(file: UploadFile, post_id: int = Form(), file_type: str = Form()) -> FileUploadVO:
    if (post := await get_post_by_id(post_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    type_enum = PostResourceTypeEnum(file_type)
    key = f'{post_id}_{type_enum}_{uuid.uuid4().hex}'
    url = await storage_put(key, io.BytesIO(await file.read()))
    resource = PostResource(name=file.filename, key=key, type=type_enum, post_id=post.id, url=url)
    session.add(resource)
    await session.flush()
    return FileUploadVO(id=resource.id, name=file.filename, key=key, location=url)
