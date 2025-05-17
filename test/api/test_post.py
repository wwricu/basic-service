from loguru import logger as log
from fastapi import status

from wwricu.domain.common import PageVO
from wwricu.domain.post import PostDetailVO

from test.test_utils import client, random


def test_create_post() -> int:
    response = client.get('/post/create')
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    post_detail = PostDetailVO.model_validate(response.json())
    return post_detail.id


def test_get_all_post() -> PageVO[PostDetailVO]:
    response = client.post('/post/all', json={})
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    return PageVO.model_validate(response.json())


def test_get_post_detail() -> PostDetailVO:
    post_preview_page = test_get_all_post()
    idx = random.randint(0, len(post_preview_page.data) - 1)
    post_preview_json = post_preview_page.data[idx]
    post_preview = PostDetailVO.model_validate(post_preview_json)
    response = client.get(f'/post/detail/{post_preview.id}')
    log.info(response.json())
    return PostDetailVO.model_validate(response.json())


def test_delete_post() -> int:
    post_id = test_create_post()
    response = client.get(f'/post/delete/{post_id}')
    assert response.status_code == status.HTTP_200_OK
    return post_id
