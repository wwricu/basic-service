from loguru import logger as log
from fastapi import status

from wwricu.domain.common import AboutPageVO, PageVO
from wwricu.domain.post import PostDetailVO

from test.test_utils import client


def test_open_get_about() -> AboutPageVO:
    response = client.get('/open/about')
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    return AboutPageVO.model_validate(response.json())


def test_open_get_post():
    response = client.post('/open/post/all', json={})
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    page = PageVO.model_validate(response.json())
    for post in page.data:
        post_detail = PostDetailVO.model_validate(post)
        log.info(post_detail)


def test_open_get_tags():
    response = client.post('/open/tags', json={})
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
