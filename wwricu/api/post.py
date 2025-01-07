import asyncio
import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, status as http_status, UploadFile

from sqlalchemy import desc, func, select, update

from wwricu.domain.common import HttpErrorDetail
from wwricu.domain.entity import BlogPost, EntityRelation, PostResource
from wwricu.domain.enum import PostStatusEnum, PostResourceTypeEnum
from wwricu.domain.input import PostUpdateRO, PostRequestRO
from wwricu.domain.output import PostDetailVO, FileUploadVO, PostDetailPageVO
from wwricu.service.common import admin_only
from wwricu.service.database import session
from wwricu.service.post import get_post_by_id, delete_post_cover, get_all_post_details, get_post_detail
from wwricu.service.storage import put_object
from wwricu.service.tag import update_category, update_tags, get_category_by_name, get_post_ids_by_tag_names


post_api = APIRouter(prefix='/post', tags=['Post Management'], dependencies=[Depends(admin_only)])


@post_api.get('/create', response_model=PostDetailVO)
async def create_post() -> PostDetailVO:
    blog_post = BlogPost(status=PostStatusEnum.DRAFT)
    session.add(blog_post)
    await session.flush()
    return PostDetailVO.model_validate(blog_post)


@post_api.post('/all', response_model=PostDetailPageVO)
async def select_post(post: PostRequestRO) -> PostDetailPageVO:
    stmt = select(BlogPost)
    if post.status is not None:
        stmt = stmt.where(BlogPost.status == post.status.value)
    if post.deleted is not None:
        stmt = stmt.where(BlogPost.deleted == post.deleted)
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

    posts_result, count = await asyncio.gather(session.scalars(post_stmt), session.scalar(count_stmt))
    all_posts = await get_all_post_details(posts_result.all())
    return PostDetailPageVO(page_index=post.page_index, page_size=post.page_size, count=count, post_details=all_posts)


@post_api.get('/detail/{post_id}', response_model=PostDetailVO | None)
async def get_post(post_id: int) -> PostDetailVO | None:
    if (post := await get_post_by_id(post_id)) is None:
        return None
    return await get_post_detail(post)


@post_api.post('/update', response_model=PostDetailVO)
async def update_post(post_update: PostUpdateRO) -> PostDetailVO:
    if (blog_post := await get_post_by_id(post_update.id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    if blog_post.cover_id is not None and blog_post.cover_id != post_update.cover_id:
        await delete_post_cover(blog_post)
    stmt = update(BlogPost).where(BlogPost.id == post_update.id).values(
        title=post_update.title,
        content=post_update.content,
        preview=post_update.preview,
        cover_id=post_update.cover_id,
        status=post_update.status,
        category_id=post_update.category_id
    )
    await session.execute(stmt)
    await update_category(blog_post, post_update.category_id)
    await update_tags(blog_post, post_update.tag_id_list)
    return await get_post_detail(blog_post)


@post_api.get('/status/{post_id}', response_model=PostDetailVO)
async def update_post_status(post_id: int, status: str) -> PostDetailVO:
    if (blog_post := await get_post_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    stmt = update(BlogPost).where(BlogPost.id == blog_post.id).values(status=PostStatusEnum(status))
    await session.execute(stmt)
    return await get_post_detail(blog_post)


@post_api.get('/delete/{post_id}', response_model=int)
async def delete_post(post_id: int):
    stmt = update(BlogPost).where(BlogPost.id == post_id).values(deleted=True)
    tag_stmt = update(EntityRelation).where(EntityRelation.src_id == post_id).values(deleted=True)
    result = await session.execute(stmt)
    await session.execute(tag_stmt)
    return result.rowcount


@post_api.post('/upload', response_model=FileUploadVO)
async def upload(file: UploadFile, post_id: int = Form(), file_type: str = Form()) -> FileUploadVO:
    if (post := await get_post_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    type_enum = PostResourceTypeEnum(file_type)
    key = f'post/{post_id}/{type_enum}_{uuid.uuid4().hex}'
    url = put_object(key, await file.read())
    resource = PostResource(name=file.filename, key=key, type=type_enum, post_id=post.id, url=url)
    session.add(resource)
    await session.flush()
    return FileUploadVO(id=resource.id, name=file.filename, key=key, location=url)
