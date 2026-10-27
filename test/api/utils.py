import uuid

from fastapi import status

from test.test_utils import client
from wwricu.domain.common import PageVO
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostDetailVO, PostPreviewVO
from wwricu.domain.tag import TagVO


def create_post() -> PostDetailVO:
    response = client.get('/admin/post/create')
    assert response.status_code == status.HTTP_200_OK
    return PostDetailVO.model_validate(response.json())


def create_post_and_delete() -> int:
    post = create_post()
    client.get(f'/admin/post/delete/{post.id}')
    return post.id


def create_tag(name: str | None = None, tag_type: TagTypeEnum = TagTypeEnum.POST_TAG) -> TagVO:
    tag_name = name or f'test_{tag_type}_{uuid.uuid4().hex[:8]}'
    response = client.post('/admin/tag/create', json={'name': tag_name, 'type': tag_type})
    assert response.status_code == status.HTTP_200_OK
    return TagVO.model_validate(response.json())


def delete_tag(tag_id: int):
    client.get(f'/admin/tag/delete/{tag_id}')


def public_post_ids() -> list[int]:
    response = client.post('/open/post/all', json={'page_index': 1, 'page_size': 10})
    assert response.status_code == status.HTTP_200_OK
    return [post.id for post in PageVO[PostPreviewVO].model_validate(response.json()).data]


def create_published_post(title: str = 'Open API Test Post') -> tuple[int, int, int]:
    uid = uuid.uuid4().hex[:8]
    tag = create_tag(f'open_tag_{uid}')
    category = create_tag(f'open_cat_{uid}', TagTypeEnum.POST_CAT)
    post = create_post()
    response = client.post('/admin/post/update', json={
        'id': post.id,
        'title': title,
        'preview': 'Test preview for open API',
        'status': PostStatusEnum.PUBLISHED,
        'content': 'Test content for open API',
        'tag_id_list': [tag.id],
        'category_id': category.id
    })
    assert response.status_code == status.HTTP_200_OK
    return post.id, tag.id, category.id


def cleanup_post_and_tags(post_id: int, tag_id: int, category_id: int):
    # /admin/post/delete refuses a published post, so revoke first or the post stays live in the database.
    client.get(f'/admin/post/status/{post_id}?status={PostStatusEnum.DRAFT}')
    client.get(f'/admin/post/delete/{post_id}')
    delete_tag(tag_id)
    delete_tag(category_id)
