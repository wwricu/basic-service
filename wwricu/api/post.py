from fastapi import APIRouter, Depends, Form, UploadFile

import wwricu.database as db
from wwricu.component.cache import cache, transient
from wwricu.database import post_db
from wwricu.domain.common import FileUploadVO, PageVO
from wwricu.domain.entity import BlogPost
from wwricu.domain.enum import PostStatusEnum, CacheKeyEnum, PostResourceTypeEnum
from wwricu.domain.post import PostDetailVO, PostRequestRO, PostUpdateRO
from wwricu.service import common_service, post_service, security_service

post_api = APIRouter(prefix='/post', tags=['Post Management'], dependencies=[Depends(security_service.require_admin)])


@post_api.get('/create', dependencies=[Depends(common_service.init_public_counts)], response_model=PostDetailVO)
async def create_post_api() -> PostDetailVO:
    blog_post = BlogPost(status=PostStatusEnum.DRAFT)
    await db.insert(blog_post)
    return PostDetailVO.model_validate(blog_post)


@post_api.post('/all', response_model=PageVO[PostDetailVO])
async def get_posts(post: PostRequestRO) -> PageVO[PostDetailVO]:
    query = await post_service.build_post_query(post)
    return await post_service.get_posts_by_query(query)


@post_api.get('/detail/{post_id}', response_model=PostDetailVO | None)
async def get_post(post_id: int) -> PostDetailVO | None:
    if (post := await post_db.find_by_id(post_id)) is None:
        return None
    return await post_service.get_post_detail(post)


@post_api.post('/update', dependencies=[Depends(common_service.init_public_counts)], response_model=PostDetailVO)
async def update_post_api(post_update: PostUpdateRO) -> PostDetailVO:
    detail = await post_service.update_post_full(post_update)
    await cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_update.id))
    await transient.delete_all()
    return detail


@post_api.get('/status/{post_id}', dependencies=[Depends(common_service.init_public_counts)], response_model=PostDetailVO)
async def update_post_status_api(post_id: int, status: PostStatusEnum) -> PostDetailVO:
    response = await post_service.update_post_status_full(post_id, status)
    await cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_id))
    await transient.delete_all()
    return response


@post_api.get('/delete/{post_id}', dependencies=[Depends(common_service.init_public_counts)], response_model=None)
async def delete_post_api(post_id: int):
    await post_service.delete_post_full(post_id)
    await cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_id))
    await transient.delete_all()


@post_api.post('/upload', response_model=FileUploadVO)
async def upload_post_file_api(file: UploadFile, post_id: int = Form(), file_type: PostResourceTypeEnum = Form()) -> FileUploadVO:
    return await post_service.upload_post_file(file, post_id, file_type)
