from fastapi import APIRouter, Depends, Form, UploadFile

from wwricu.component.cache import cache, transient
from wwricu.database.common import insert
from wwricu.database.post import get_post_by_id
from wwricu.domain.common import FileUploadVO, PageVO
from wwricu.domain.entity import BlogPost
from wwricu.domain.enum import PostStatusEnum, CacheKeyEnum
from wwricu.domain.post import PostDetailVO, PostRequestRO, PostUpdateRO
from wwricu.function.common import reset_system_count
from wwricu.function.post import build_post_query, delete_post_full, get_post_detail, get_posts_by_query, update_post_full, update_post_status_full, upload_post_file
from wwricu.function.security import admin_only

post_api = APIRouter(prefix='/post', tags=['Post Management'], dependencies=[Depends(admin_only)])


@post_api.get('/create', dependencies=[Depends(reset_system_count)], response_model=PostDetailVO)
async def create_post_api() -> PostDetailVO:
    blog_post = BlogPost(status=PostStatusEnum.DRAFT)
    await insert(blog_post)
    return PostDetailVO.model_validate(blog_post)


@post_api.post('/all', response_model=PageVO[PostDetailVO])
async def get_posts(post: PostRequestRO) -> PageVO[PostDetailVO]:
    query = await build_post_query(post)
    return await get_posts_by_query(query)


@post_api.get('/detail/{post_id}', response_model=PostDetailVO | None)
async def get_post(post_id: int) -> PostDetailVO | None:
    if (post := await get_post_by_id(post_id)) is None:
        return None
    return await get_post_detail(post)


@post_api.post('/update', dependencies=[Depends(reset_system_count)], response_model=PostDetailVO)
async def update_post_api(post_update: PostUpdateRO) -> PostDetailVO:
    detail = await update_post_full(post_update)
    await cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_update.id))
    await transient.delete_all()
    return detail


@post_api.get('/status/{post_id}', dependencies=[Depends(reset_system_count)], response_model=PostDetailVO)
async def update_post_status_api(post_id: int, status: str) -> PostDetailVO:
    response = await update_post_status_full(post_id, status)
    await cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_id))
    await transient.delete_all()
    return response


@post_api.get('/delete/{post_id}', dependencies=[Depends(reset_system_count)], response_model=None)
async def delete_post_api(post_id: int):
    await delete_post_full(post_id)
    await cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_id))
    await transient.delete_all()


@post_api.post('/upload', response_model=FileUploadVO)
async def upload_post_file_api(file: UploadFile, post_id: int = Form(), file_type: str = Form()) -> FileUploadVO:
    return await upload_post_file(file, post_id, file_type)
