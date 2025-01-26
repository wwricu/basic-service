from loguru import logger as log
from fastapi import status

from fastapi.testclient import TestClient
from sqlalchemy import select

from wwricu.domain.entity import PostTag, EntityRelation, BlogPost
from wwricu.domain.enum import TagTypeEnum
from wwricu.main import app
from wwricu.service.post import get_posts_preview


client = TestClient(app)



def test_create_post():
    response = client.get('/post/create')
    assert response.status_code == status.HTTP_200_OK
    log.info(response.json())


def test_get_post_detail():
    response = client.get('/post/detail/1')
    assert response.status_code == status.HTTP_200_OK
    log.info(response.json())


def test_get_all_post():
    get_posts_preview([])
    cat_stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_CAT).where(
        PostTag.deleted == False).where(
        PostTag.id.in_((1, 2))
    )
    tag_stmt = select(PostTag).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        PostTag.deleted == False).join(
        EntityRelation, PostTag.id == EntityRelation.dst_id).join(
        BlogPost, EntityRelation.src_id == BlogPost.id
    )
    print(tag_stmt)
    print(cat_stmt)
