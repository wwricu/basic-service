import uuid

from fastapi import status

from test.test_utils import client
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostDetailVO
from wwricu.domain.tag import TagVO


def create_post() -> PostDetailVO:
    response = client.post('/admin/post/create')
    assert response.status_code == status.HTTP_200_OK
    return PostDetailVO.model_validate(response.json())


def create_tag(tag_type: TagTypeEnum) -> TagVO:
    name = f'test_{tag_type}_{uuid.uuid4().hex[:8]}'
    response = client.post('/admin/tag/create', json={'name': name, 'type': tag_type})
    assert response.status_code == status.HTTP_200_OK
    return TagVO.model_validate(response.json())


def delete_tag(tag_id: int):
    assert client.delete(f'/admin/tag/delete/{tag_id}').status_code == status.HTTP_200_OK


def cleanup_post_and_tags(post_id: int, tag_id: int, category_id: int):
    # /admin/post/delete refuses a published post, so revoke first or the post stays live in the database.
    client.post(f'/admin/post/status/{post_id}', json={'status': PostStatusEnum.DRAFT})
    client.delete(f'/admin/post/delete/{post_id}')
    delete_tag(tag_id)
    delete_tag(category_id)
