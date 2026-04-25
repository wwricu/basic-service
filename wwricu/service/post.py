import asyncio
import uuid

from fastapi import HTTPException, UploadFile, status as http_status

from wwricu.database import post_db, tag_db, res_db
from wwricu.database.common import insert
from wwricu.domain.common import FileUploadVO, PageVO
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import PostResourceTypeEnum, PostStatusEnum
from wwricu.domain.post import PostDetailVO, PostQueryDTO, PostRequestRO, PostResourceVO, PostUpdateRO
from wwricu.domain.tag import TagVO
from wwricu.domain.entity import BlogPost, PostResource
from wwricu.component.database import transaction
from wwricu.component.storage import oss_public
from wwricu.service.tag import get_post_tags, update_tag_count, update_post_tags, update_category, get_posts_category


async def build_post_query(post: PostRequestRO, *, public: bool = False) -> PostQueryDTO:
    query = PostQueryDTO(
        status=PostStatusEnum.PUBLISHED if public else post.status,
        deleted=False if public else post.deleted,
        page_size=post.page_size,
        page_index=post.page_index,
        post_ids=await post_db.get_post_ids_by_tag_names(post.tag_list) if post.tag_list else None
    )
    if post.category and (category := await tag_db.get_category(name=post.category)):
        query.category_id = category.id
    return query


async def get_posts_by_query(query: PostQueryDTO) -> PageVO[PostDetailVO]:
    posts = await post_db.get_posts_by_example(query)
    return PageVO[PostDetailVO](
        page_size=query.page_size,
        page_index=query.page_index,
        count=await post_db.get_posts_count(query),
        data=await get_posts_preview(posts)
    )


async def delete_post_cover(post: BlogPost):
    """HARD DELETE the resource because we are using free object storage"""
    if (resource := await res_db.get_post_cover(post.cover_id)) is None:
        return
    await res_db.delete_resource(resource.id)
    asyncio.create_task(oss_public.delete(resource.key))


async def get_post_detail(blog_post: BlogPost | None) -> PostDetailVO:
    if blog_post is None:
        raise ValueError
    category = await tag_db.get_category(category_id=blog_post.category_id)
    tags = await get_post_tags(blog_post)
    cover = await res_db.get_post_cover(blog_post.cover_id)
    post_detail = PostDetailVO.model_validate(blog_post)
    post_detail.tag_list = list(map(TagVO.model_validate, tags))

    if category is not None:
        post_detail.category = TagVO.model_validate(category)
    if cover is not None:
        post_detail.cover = PostResourceVO.model_validate(cover)
    return post_detail


async def get_posts_preview(post_list: list[BlogPost]) -> list[PostDetailVO]:
    """Generate post preview from BlogPost list"""
    categories = await get_posts_category(post_list)
    tags = await tag_db.get_tags_by_posts(post_list)
    covers = await res_db.get_posts_cover(post_list)

    def generator(post: BlogPost) -> PostDetailVO:
        detail = PostDetailVO(
            id=post.id,
            title=post.title,
            preview=post.preview,
            tag_list=[TagVO.model_validate(tag) for tag in tags.get(post.id, [])],
            status=PostStatusEnum(post.status),
            create_time=post.create_time,
            update_time=post.update_time
        )
        if category := categories.get(post.id):
            detail.category = TagVO.model_validate(category)
        if cover := covers.get(post.id):
            detail.cover = PostResourceVO.model_validate(cover)
        return detail

    return list(map(generator, post_list))


@transaction
async def update_post_full(post_update: PostUpdateRO) -> PostDetailVO:
    if (blog_post := await post_db.get_post_by_id(post_update.id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    if blog_post.cover_id is not None and blog_post.cover_id != post_update.cover_id:
        await delete_post_cover(blog_post)
    await update_category(blog_post, post_update)
    await update_post_tags(blog_post, post_update)
    await post_db.update_post_selective(
        post_update.id,
        title=post_update.title,
        content=post_update.content,
        preview=post_update.preview,
        cover_id=post_update.cover_id,
        status=post_update.status,
        category_id=post_update.category_id
    )
    blog_post = await post_db.get_post_by_id(post_update.id)
    return await get_post_detail(blog_post)


async def update_post_status_full(post_id: int, new_status: PostStatusEnum) -> PostDetailVO:
    if (blog_post := await post_db.get_post_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    await post_db.update_post_selective(blog_post.id, status=new_status)
    blog_post = await post_db.get_post_by_id(post_id)
    return await get_post_detail(blog_post)


@transaction
async def delete_post_full(post_id: int) -> None:
    if (post := await post_db.get_post_by_id(post_id)) is None:
        return
    if post.status == PostStatusEnum.PUBLISHED:
        await tag_db.update_category_count(post, -1)
        await update_tag_count(post, -1)
    await post_db.update_post_selective(post.id, deleted=True)


async def upload_post_file(file: UploadFile, post_id: int, file_type: PostResourceTypeEnum) -> FileUploadVO:
    if (post := await post_db.get_post_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    key = f'post/{post_id}/{file_type}_{uuid.uuid4().hex}'
    url = await oss_public.put(key, await file.read())
    resource = PostResource(name=file.filename, key=key, type=file_type, post_id=post.id, url=url)
    await insert(resource)
    return FileUploadVO(id=resource.id, name=file.filename, key=key, location=url)
