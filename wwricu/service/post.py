import uuid

from bs4 import BeautifulSoup
from fastapi import HTTPException, UploadFile, status as http_status
from loguru import logger as log

from wwricu.component.database import transaction
from wwricu.component.storage import oss_public
from wwricu.config import app_config
from wwricu.database import common_db, post_db, tag_db, res_db
from wwricu.domain.common import FileUploadVO, PageVO, TrashBinRO
from wwricu.domain.constant import HttpErrorDetail, CommonConstant
from wwricu.domain.entity import BlogPost, PostResource, PostTag, EntityRelation
from wwricu.domain.enum import PostResourceTypeEnum, PostStatusEnum, TagTypeEnum, RelationTypeEnum
from wwricu.domain.post import PostDetailVO, PostQueryDTO, PostRequestRO, PostResourceVO, PostUpdateRO
from wwricu.domain.tag import TagVO, TagUpdateDTO, TagQueryDTO


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
    tags = await get_tags(blog_post)
    cover = await res_db.find_by_id(blog_post.cover_id, PostResourceTypeEnum.COVER_IMAGE)
    post_detail = PostDetailVO.model_validate(blog_post)
    post_detail.tag_list = list(map(TagVO.model_validate, tags))

    if category is not None:
        post_detail.category = TagVO.model_validate(category)
    if cover is not None:
        post_detail.cover = PostResourceVO.model_validate(cover)
    return post_detail


async def get_preview(post_list: list[BlogPost]) -> list[PostDetailVO]:
    """Generate post preview from BlogPost list"""
    categories = await batch_get_category(post_list)
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

    resources = await res_db.find_by_post_id(post.id)
    bef_keys = {res.key for res in resources if res.id != new_post.cover_id}
    aft_keys = set()
    for img in BeautifulSoup(new_post.content, CommonConstant.HTML_PARSER).find_all(CommonConstant.IMG_TAG):
        src = img.get(CommonConstant.SRC_PROP)
        if isinstance(src, str) and (key := oss_public.get_key_from_url(src)):
            aft_keys.add(key)

    if delete_keys := list(bef_keys - aft_keys):
        await res_db.delete_by_keys(delete_keys)
        log.info(f'delete resource {delete_keys}')

    tag_update = TagUpdateDTO(category_id=new_post.category_id, tag_id_list=new_post.tag_id_list, status=new_post.status)
    await update_category(post, tag_update)
    await update_tags(post, tag_update)
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
        tag_id_list=await tag_db.find_ids_by_post_id(blog_post.id),
        status=status
    )

    await update_category(blog_post, tag_update)
    await update_tags(blog_post, tag_update)
    await post_db.update_selective(blog_post.id, status=tag_update.status)


async def update_tags(post: BlogPost, tag_update: TagUpdateDTO):
    tags = await tag_db.find_by_criteria(TagQueryDTO(tag_ids=tag_update.tag_id_list, type=TagTypeEnum.POST_TAG))
    tag_ids, update_tag_ids = {tag.id for tag in await get_tags(post)}, set(tag_update.tag_id_list)

    if tag_ids != update_tag_ids:
        await post_db.delete_tags(post.id)
        relations = [EntityRelation(src_id=post.id, dst_id=t.id, type=RelationTypeEnum.POST_TAG) for t in tags]
        await common_db.insert_all(relations)

    bef_tag_ids, aft_tag_ids = set(), set()
    if post.status == PostStatusEnum.PUBLISHED:
        bef_tag_ids = tag_ids
    if tag_update.status == PostStatusEnum.PUBLISHED:
        aft_tag_ids = update_tag_ids
    await tag_db.update_tag_post_count(bef_tag_ids, aft_tag_ids)


async def get_tags(post: BlogPost) -> list[PostTag]:
    tag_ids = await tag_db.find_ids_by_post_id(post.id)
    return await tag_db.find_by_criteria(TagQueryDTO(tag_ids=tag_ids, type=TagTypeEnum.POST_TAG))


async def update_category(post: BlogPost, count_update: TagUpdateDTO):
    if post.category_id != count_update.category_id:
        category = await tag_db.find_category(category_id=count_update.category_id)
        await post_db.update_selective(post.id, category_id=category.id if category else None)

    bef_category_id, aft_category_id = None, None
    if post.status == PostStatusEnum.PUBLISHED:
        bef_category_id = post.category_id
    if count_update.status == PostStatusEnum.PUBLISHED:
        aft_category_id = count_update.category_id
    await tag_db.update_category_post_count(bef_category_id, aft_category_id)


async def batch_get_category(post_list: list[BlogPost]) -> dict[int, PostTag]:
    if not (category_ids := [post.category_id for post in post_list if post.category_id]):
        return {}
    categories = await tag_db.find_by_criteria(TagQueryDTO(tag_ids=category_ids, type=TagTypeEnum.POST_CAT))
    category_dict = {cat.id: cat for cat in categories}
    return {post.id: tag for post in post_list if (tag := category_dict.get(post.category_id))}


async def upload_file(file: UploadFile, post_id: int, file_type: PostResourceTypeEnum) -> FileUploadVO:
    if (post := await post_db.find_by_id(post_id)) is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=HttpErrorDetail.POST_NOT_FOUND)
    if file.size is None or file.size > app_config.max_upload_size:
        raise HTTPException(http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    key = f'post/{post_id}/{file_type}_{uuid.uuid4().hex}'
    url = await oss_public.put(key, await file.read())
    resource = PostResource(name=file.filename, key=key, type=file_type, post_id=post.id, url=url)
    await common_db.insert(resource)
    log.info(f'upload file {file.filename} to {post_id=} {file.size=} {url=}')
    return FileUploadVO(id=resource.id, name=file.filename, key=key, location=url)


@transaction
async def process_trash(trash_bin: TrashBinRO):
    if trash_bin.delete:
        resources = await res_db.find_by_post_id(trash_bin.id)
        await res_db.delete_by_keys([res.key for res in resources])
        await common_db.hard_delete(BlogPost, trash_bin.id)
    else:
        await post_db.update_selective(trash_bin.id, deleted=False)


async def process_resource_trash(trash_bin: TrashBinRO):
    if trash_bin.delete is False:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN)

    resource = await res_db.find_by_id(trash_bin.id, deleted=True)
    await common_db.hard_delete(PostResource, trash_bin.id)

    if resource:
        await oss_public.delete(resource.key)
        log.warning(f'delete resource {resource.key}')
