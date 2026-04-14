from loguru import logger as log
from fastapi import status

from wwricu.domain.common import AboutPageVO, PageVO
from wwricu.domain.post import PostDetailVO

from test.test_utils import client


def test_open_get_about():
    response = client.get('/open/about')
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    AboutPageVO.model_validate(response.json())


def test_open_get_post():
    response = client.post('/open/post/all', json={})
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    page = PageVO.model_validate(response.json())
    for post in page.data:
        post_detail = PostDetailVO.model_validate(post)
        log.info(post_detail)


def test_open_get_tags():
    response = client.get('/open/tags/post_tag')
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK


def test_open_get_post_detail():
    # Get a post id from list first
    list_response = client.post('/open/post/all', json={})
    assert list_response.status_code == status.HTTP_200_OK
    page = PageVO.model_validate(list_response.json())
    assert len(page.data) > 0
    post_id = PostDetailVO.model_validate(page.data[0]).id
    # Get post detail
    response = client.get(f'/open/post/detail/{post_id}')
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    PostDetailVO.model_validate(response.json())


def test_open_get_post_detail_not_found():
    response = client.get('/open/post/detail/99999')
    assert response.status_code == status.HTTP_404_NOT_FOUND
