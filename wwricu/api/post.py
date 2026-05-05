import secrets

from fastapi import APIRouter, Depends, Form, UploadFile, HTTPException, status as http_status

from wwricu.component.cache import query_cache, post_cache
from wwricu.database import common_db, post_db
from wwricu.domain.common import FileUploadVO, PageVO
from wwricu.domain.entity import BlogPost
from wwricu.domain.enum import PostStatusEnum, CacheKeyEnum, PostResourceTypeEnum
from wwricu.domain.post import PostDetailVO, PostRequestRO, PostUpdateRO
from wwricu.service import common_service, post_service, security_service

post_api = APIRouter(prefix='/post', tags=['Post Management'], dependencies=[Depends(security_service.require_admin)])


@post_api.get('/create', response_model=PostDetailVO)
async def create_post_api() -> PostDetailVO:
    while await post_db.find_by_id(post_id := 1_000_000_000 + secrets.randbelow(9_000_000_000)):
        pass
    blog_post = BlogPost(id=post_id, status=PostStatusEnum.DRAFT)
    await common_db.insert(blog_post)
    return PostDetailVO.model_validate(blog_post)


@post_api.post('/all', response_model=PageVO[PostDetailVO])
async def get_posts(post: PostRequestRO) -> PageVO[PostDetailVO]:
    query = await post_service.build_query(post)
    return await post_service.list_by_query(query)


@post_api.get('/detail/{post_id}', response_model=PostDetailVO | None)
async def get_post(post_id: int) -> PostDetailVO | None:
    if (post := await post_db.find_by_id(post_id)) is None:
        return None
    return await post_service.get_detail(post)


@post_api.post('/update', dependencies=[Depends(common_service.reset_sys_config)], response_model=PostDetailVO)
async def update_post_api(post_update: PostUpdateRO) -> PostDetailVO:
    detail = await post_service.update(post_update)
    await post_cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_update.id))
    await query_cache.delete_all()
    return detail


@post_api.get('/status/{post_id}', dependencies=[Depends(common_service.reset_sys_config)], response_model=None)
async def update_post_status_api(post_id: int, status: PostStatusEnum):
    await post_service.update_status(post_id, status=status)
    await post_cache.delete(CacheKeyEnum.POST_DETAIL.format(id=post_id))
    await query_cache.delete_all()


@post_api.get('/delete/{post_id}', dependencies=[Depends(common_service.reset_sys_config)], response_model=None)
async def delete_post_draft_api(post_id: int):
    if (post := await post_db.find_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND)
    if post.status == PostStatusEnum.PUBLISHED:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)
    await post_db.update_selective(post_id, deleted=True)


@post_api.post('/upload', response_model=FileUploadVO)
async def upload_post_file_api(file: UploadFile, post_id: int = Form(), file_type: PostResourceTypeEnum = Form()) -> FileUploadVO:
    return await post_service.upload_file(file, post_id, file_type)
