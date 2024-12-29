from loguru import logger as log
from fastapi import status

from wwricu.domain.enum import PostStatusEnum
from wwricu.domain.input import PostUpdateRO, BatchIdRO

from test.test_client import client


def test_create_post():
    response = client.get('/post/create')
    assert response.status_code == status.HTTP_200_OK
    log.info(response.json())

# {'id': 3, 'title': 'Test Title', 'cover': None, 'content': None, 'tag_list': [], 'category': None, 'status': 'draft', 'create_time': '2024-12-13T15:38:20', 'update_time': '2024-12-13T15:38:20'}
def test_patch_post():
    post = PostUpdateRO(
        id=27,
        title='Test Title',
        status=PostStatusEnum.PUBLISHED
    )
    response = client.post('/post/patch', json=post.model_dump())
    log.info(response.json())


def test_delete_post():
    batch = BatchIdRO(id_list=[27, 26])
    response = client.post('/post/delete', json=batch.model_dump())
    assert response.status_code == status.HTTP_200_OK
    log.info(response.json())


def test_get_post_detail():
    response = client.get('/post/detail/1')
    assert response.status_code == status.HTTP_200_OK
    log.info(response.json())
