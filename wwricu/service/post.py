import uuid

from bs4 import BeautifulSoup
from fastapi import HTTPException, UploadFile, status as http_status
from loguru import logger as log

from wwricu.component.database import transaction
from wwricu.component.storage import oss_public
from wwricu.database import common_db, post_db, tag_db, res_db
from wwricu.domain.common import FileUploadVO, PageVO
from wwricu.domain.constant import HttpErrorDetail, CommonConstant
from wwricu.domain.entity import BlogPost, PostResource
from wwricu.domain.enum import PostResourceTypeEnum, PostStatusEnum
from wwricu.domain.post import PostDetailVO, PostQueryDTO, PostRequestRO, PostResourceVO, PostUpdateRO
from wwricu.domain.tag import TagVO, TagUpdateDTO
from wwricu.service.tag import get_post_tags, update_tag_count, update_post_tags, update_post_category, get_posts_category


async def build_query(post: PostRequestRO, *, public: bool = False) -> PostQueryDTO:
    query = PostQueryDTO(
        status=PostStatusEnum.PUBLISHED if public else post.status,
        deleted=False if public else post.deleted,
        page_size=post.page_size,
        page_index=post.page_index,
        post_ids=await post_db.find_by_ids_by_tags(post.tag_list) if post.tag_list else None
    )
    if post.category and (category := await tag_db.find_category(name=post.category)):
        query.category_id = category.id
    return query


async def list_by_query(query: PostQueryDTO) -> PageVO[PostDetailVO]:
    posts = await post_db.find_by_criteria(query)
    return PageVO[PostDetailVO](
        page_size=query.page_size,
        page_index=query.page_index,
        count=await post_db.count(query),
        data=await get_preview(posts)
    )


async def get_detail(blog_post: BlogPost | None) -> PostDetailVO:
    if blog_post is None:
        raise ValueError
    category = await tag_db.find_category(category_id=blog_post.category_id)
    tags = await get_post_tags(blog_post)
    cover = await res_db.find_post_cover(blog_post.cover_id)
    post_detail = PostDetailVO.model_validate(blog_post)
    post_detail.tag_list = list(map(TagVO.model_validate, tags))

    if category is not None:
        post_detail.category = TagVO.model_validate(category)
    if cover is not None:
        post_detail.cover = PostResourceVO.model_validate(cover)
    return post_detail


async def get_preview(post_list: list[BlogPost]) -> list[PostDetailVO]:
    """Generate post preview from BlogPost list"""
    categories = await get_posts_category(post_list)
    tags = await tag_db.find_tags_by_posts(post_list)
    covers = await res_db.find_posts_cover(post_list)

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
async def update(new_post: PostUpdateRO) -> PostDetailVO:
    if (post := await post_db.find_by_id(new_post.id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)

    bef_keys = await get_resource_keys(post.content)
    aft_keys = await get_resource_keys(new_post.content)
    if delete_keys := list(bef_keys - aft_keys):
        await res_db.delete_resources(delete_keys)
        log.info(f'delete resource {delete_keys}')

    if post.cover_id is not None and post.cover_id != new_post.cover_id and (res := await res_db.find_post_cover(post.cover_id)):
        await res_db.delete_resources([res.key])
        log.info(f'delete cover {res.key}')

    tag_update = TagUpdateDTO(category_id=new_post.category_id, tag_id_list=new_post.tag_id_list, status=new_post.status)
    await update_post_category(post, tag_update)
    await update_post_tags(post, tag_update)
    await post_db.update_selective(
        new_post.id,
        title=new_post.title,
        content=new_post.content,
        preview=new_post.preview,
        cover_id=new_post.cover_id,
        status=new_post.status,
        category_id=new_post.category_id
    )

    post = await post_db.find_by_id(new_post.id)
    return await get_detail(post)


@transaction
async def update_status(post_id: int, status: PostStatusEnum):
    if (blog_post := await post_db.find_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)

    tag_update = TagUpdateDTO(
        category_id=blog_post.category_id,
        tag_id_list=await tag_db.find_tag_ids_by_post_id(blog_post.id),
        status=status
    )

    await update_post_category(blog_post, tag_update)
    await update_post_tags(blog_post, tag_update)
    await post_db.update_selective(blog_post.id, status=tag_update.status)


@transaction
async def update_deleted(post_id: int, deleted: bool = True):
    if (post := await post_db.find_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    if post.deleted == deleted:
        return
    if deleted is True and post.status == PostStatusEnum.PUBLISHED:
        raise HTTPException(status_code=http_status.HTTP_406_NOT_ACCEPTABLE, detail=HttpErrorDetail.DELETE_PUBLISH)
    if not deleted:
        await post_db.update_selective(post_id, deleted=False)
    if (post := await post_db.find_by_id(post_id)) is None:
        return
    delta = -1 if deleted else 1
    if post.status == PostStatusEnum.PUBLISHED:
        await tag_db.update_category_count(post, delta)
        await update_tag_count(post, delta)
    if deleted:
        await post_db.update_selective(post.id, deleted=True)


async def upload_file(file: UploadFile, post_id: int, file_type: PostResourceTypeEnum) -> FileUploadVO:
    if (post := await post_db.find_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    key = f'post/{post_id}/{file_type}_{uuid.uuid4().hex}'
    url = await oss_public.put(key, await file.read())
    resource = PostResource(name=file.filename, key=key, type=file_type, post_id=post.id, url=url)
    await common_db.insert(resource)
    return FileUploadVO(id=resource.id, name=file.filename, key=key, location=url)


async def get_resource_keys(content: str) -> set[str]:
    soup = BeautifulSoup(content, CommonConstant.HTML_PARSER)
    keys = set()
    for img in soup.find_all(CommonConstant.IMG_TAG):
        src = img.get(CommonConstant.SRC_PROP)
        if isinstance(src, str) and (key := oss_public.get_key_from_url(src)):
            keys.add(key)
    return keys
