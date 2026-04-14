import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status as http_status

from wwricu.database.category import get_category_by_name, update_category_count
from wwricu.database.common import insert
from wwricu.database.post import get_post_ids_by_tag_names, get_post_by_id, update_post_selective, \
    update_post, get_posts_by_example, get_posts_count
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.entity import BlogPost, PostResource
from wwricu.domain.enum import PostResourceTypeEnum, PostStatusEnum, CacheKeyEnum
from wwricu.domain.post import PostDetailVO, PostRequestRO, PostUpdateRO, PostQueryDTO
from wwricu.domain.common import FileUploadVO, PageVO
from wwricu.component.cache import cache, transient
from wwricu.service.common import reset_system_count
from wwricu.service.category import update_category
from wwricu.component.database import transaction
from wwricu.service.post import delete_post_cover, get_posts_preview, get_post_detail
from wwricu.service.security import admin_only
from wwricu.component.storage import oss_public
from wwricu.service.tag import update_tags, update_tag_count

post_api = APIRouter(prefix='/post', tags=['Post Management'], dependencies=[Depends(admin_only)])


@post_api.get('/create', dependencies=[Depends(reset_system_count)], response_model=PostDetailVO)
async def create_post() -> PostDetailVO:
    blog_post = BlogPost(status=PostStatusEnum.DRAFT)
    await insert(blog_post)
    return PostDetailVO.model_validate(blog_post)


@post_api.post('/all', response_model=PageVO[PostDetailVO])
async def get_posts(post: PostRequestRO) -> PageVO[PostDetailVO]:
    query = PostQueryDTO(
        status=post.status,
        deleted=post.deleted,
        page_size=post.page_size,
        page_index=post.page_index,
        post_ids = await get_post_ids_by_tag_names(post.tag_list) if post.tag_list else None
    )
    if post.category and (category := await get_category_by_name(post.category)):
        query.category_id = category.id
    posts = await get_posts_by_example(query)
    return PageVO[PostDetailVO](
        page_size=post.page_size,
        page_index=post.page_index,
        count=await get_posts_count(query),
        data=await get_posts_preview(posts)
    )


@post_api.get('/detail/{post_id}', response_model=PostDetailVO | None)
async def get_post(post_id: int) -> PostDetailVO | None:
    if (post := await get_post_by_id(post_id)) is None:
        return None
    return await get_post_detail(post)


@post_api.post('/update', dependencies=[Depends(reset_system_count)], response_model=PostDetailVO)
async def update_post_api(post_update: PostUpdateRO) -> PostDetailVO:
    if (blog_post := await get_post_by_id(post_update.id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)

    async with transaction():
        if blog_post.cover_id is not None and blog_post.cover_id != post_update.cover_id:
            await delete_post_cover(blog_post)
        await update_category(blog_post, post_update)
        await update_tags(blog_post, post_update)
        await update_post(post_update)

    await cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_update.id))
    await transient.delete_all()

    return await get_post_detail(blog_post)


@post_api.get('/status/{post_id}', dependencies=[Depends(reset_system_count)], response_model=PostDetailVO)
async def update_post_status_api(post_id: int, status: str) -> PostDetailVO:
    if (blog_post := await get_post_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    await update_post_selective(blog_post.id, status=PostStatusEnum(status))

    await cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_id))
    await transient.delete_all()

    return await get_post_detail(blog_post)


@post_api.get('/delete/{post_id}', dependencies=[Depends(reset_system_count)], response_model=None)
async def delete_post_api(post_id: int):
    if (post := await get_post_by_id(post_id)) is None:
        return

    async with transaction():
        if post.status == PostStatusEnum.PUBLISHED:
            await update_category_count(post, -1)
            await update_tag_count(post, -1)
        await update_post_selective(post.id, deleted=True)

    await cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_id))
    await transient.delete_all()


@post_api.post('/upload', response_model=FileUploadVO)
async def upload_post_file_api(file: UploadFile, post_id: int = Form(), file_type: str = Form()) -> FileUploadVO:
    if (post := await get_post_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    type_enum = PostResourceTypeEnum(file_type)
    key = f'post/{post_id}/{type_enum}_{uuid.uuid4().hex}'
    url = oss_public.put(key, await file.read())
    resource = PostResource(name=file.filename, key=key, type=type_enum, post_id=post.id, url=url)
    await insert(resource)
    return FileUploadVO(id=resource.id, name=file.filename, key=key, location=url)
