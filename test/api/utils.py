import uuid

from fastapi import status

from test.test_utils import client
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostDetailVO
from wwricu.domain.tag import TagVO


def set_password(password: str):
    response = client.post('/manage/user', json={'password': password})
    assert response.status_code == status.HTTP_200_OK


def reset_credentials():
    response = client.post('/manage/user', json={'reset': True})
    assert response.status_code == status.HTTP_200_OK


def create_post() -> PostDetailVO:
    response = client.get('/post/create')
    assert response.status_code == status.HTTP_200_OK
    return PostDetailVO.model_validate(response.json())


def create_published_post() -> PostDetailVO:
    post = create_post()
    tag_response = client.post('/tag/create', json={'name': f'post_test_{uuid.uuid4().hex[:8]}', 'type': TagTypeEnum.POST_TAG})
    tag = TagVO.model_validate(tag_response.json())
    cat_response = client.post('/tag/create', json={'name': f'post_test_cat_{uuid.uuid4().hex[:8]}', 'type': TagTypeEnum.POST_CAT})
    category = TagVO.model_validate(cat_response.json())
    update_data = {
        'id': post.id,
        'title': f'Published Post {uuid.uuid4().hex[:8]}',
        'preview': 'Test preview content',
        'status': PostStatusEnum.PUBLISHED,
        'content': 'Test post content for published post',
        'tag_id_list': [tag.id],
        'category_id': category.id
    }
    response = client.post('/post/update', json=update_data)
    assert response.status_code == status.HTTP_200_OK
    return PostDetailVO.model_validate(response.json())


def create_post_and_delete() -> int:
    create_response = client.get('/post/create')
    post = PostDetailVO.model_validate(create_response.json())
    client.get(f'/post/delete/{post.id}')
    return post.id


def create_tag(name: str | None = None, tag_type: TagTypeEnum = TagTypeEnum.POST_TAG) -> TagVO:
    tag_name = name or f'test_{tag_type}_{uuid.uuid4().hex[:8]}'
    response = client.post('/tag/create', json={'name': tag_name, 'type': tag_type})
    assert response.status_code == status.HTTP_200_OK
    return TagVO.model_validate(response.json())


def delete_tag(tag_id: int):
    client.get(f'/tag/delete/{tag_id}')


def create_tag_and_delete() -> int:
    tag_response = client.post('/tag/create', json={'name': f'trash_test_{uuid.uuid4().hex[:8]}', 'type': TagTypeEnum.POST_TAG})
    tag = TagVO.model_validate(tag_response.json())
    client.get(f'/tag/delete/{tag.id}')
    return tag.id


def create_published_post_with_tag() -> tuple[int, int, int]:
    uid = uuid.uuid4().hex[:8]
    create_tag_response = client.post('/tag/create', json={'name': f'open_tag_{uid}', 'type': TagTypeEnum.POST_TAG})
    tag = TagVO.model_validate(create_tag_response.json())
    create_cat_response = client.post('/tag/create', json={'name': f'open_cat_{uid}', 'type': TagTypeEnum.POST_CAT})
    category = TagVO.model_validate(create_cat_response.json())
    create_post_response = client.get('/post/create')
    post = PostDetailVO.model_validate(create_post_response.json())
    update_data = {
        'id': post.id,
        'title': 'Open API Test Post',
        'preview': 'Test preview for open API',
        'status': PostStatusEnum.PUBLISHED,
        'content': 'Test content for open API',
        'tag_id_list': [tag.id],
        'category_id': category.id
    }
    client.post('/post/update', json=update_data)
    return post.id, tag.id, category.id


def cleanup_post_and_tags(post_id: int, tag_id: int, category_id: int):
    client.get(f'/post/delete/{post_id}')
    client.get(f'/tag/delete/{tag_id}')
    client.get(f'/tag/delete/{category_id}')
