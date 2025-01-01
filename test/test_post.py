from loguru import logger as log
from fastapi import status

from test.test_client import client


def test_create_post():
    response = client.get('/post/create')
    assert response.status_code == status.HTTP_200_OK
    log.info(response.json())


def test_get_post_detail():
    response = client.get('/post/detail/1')
    assert response.status_code == status.HTTP_200_OK
    log.info(response.json())
