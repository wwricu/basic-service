from fastapi import status
from loguru import logger as log

from test.api.utils import cleanup_post_and_tags, create_published_post_with_tag
from test.test_utils import client
from wwricu.domain.common import AboutPageVO, PageVO
from wwricu.domain.enum import TagTypeEnum
from wwricu.domain.post import PostDetailVO
from wwricu.domain.tag import TagVO


def test_open_get_about():
    response = client.get('/open/about')
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    about = AboutPageVO.model_validate(response.json())
    assert isinstance(about.content, (str, type(None)))


def test_open_get_posts():
    response = client.post('/open/post/all', json={})
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    page = PageVO.model_validate(response.json())
    for post in page.data:
        PostDetailVO.model_validate(post)


def test_open_get_posts_pagination():
    response = client.post('/open/post/all', json={'page_index': 1, 'page_size': 5})
    assert response.status_code == status.HTTP_200_OK
    page = PageVO[PostDetailVO].model_validate(response.json())
    assert page.page_index == 1
    assert page.page_size == 5
    assert page.count >= 0


def test_open_get_post_detail_not_found():
    response = client.get('/open/post/detail/99999')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_open_get_post_detail_draft_not_found():
    create_response = client.get('/post/create')
    post = PostDetailVO.model_validate(create_response.json())
    try:
        response = client.get(f'/open/post/detail/{post.id}')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    finally:
        client.get(f'/post/delete/{post.id}')


def test_open_get_tags():
    for tag_type in [TagTypeEnum.POST_TAG, TagTypeEnum.POST_CAT]:
        response = client.get(f'/open/tags/{tag_type}')
        log.info(response.json())
        assert response.status_code == status.HTTP_200_OK
        [TagVO.model_validate(t) for t in response.json()]


def test_open_get_posts_with_tag_filter():
    post_id, tag_id, category_id = create_published_post_with_tag()
    try:
        tag_response = client.get('/open/tags/post_tag')
        tags = [TagVO.model_validate(t) for t in tag_response.json()]
        test_tag = next((t for t in tags if t.id == tag_id), None)
        assert test_tag is not None
        response = client.post('/open/post/all', json={'tag_list': [test_tag.name]})
        assert response.status_code == status.HTTP_200_OK
        page = PageVO[PostDetailVO].model_validate(response.json())
        post_ids = [PostDetailVO.model_validate(p).id for p in page.data]
        assert post_id in post_ids
    finally:
        cleanup_post_and_tags(post_id, tag_id, category_id)


def test_open_get_posts_with_category_filter():
    post_id, tag_id, category_id = create_published_post_with_tag()
    try:
        cat_response = client.get('/open/tags/post_category')
        cats = [TagVO.model_validate(t) for t in cat_response.json()]
        test_cat = next((c for c in cats if c.id == category_id), None)
        assert test_cat is not None
        response = client.post('/open/post/all', json={'category': test_cat.name})
        assert response.status_code == status.HTTP_200_OK
        page = PageVO[PostDetailVO].model_validate(response.json())
        post_ids = [PostDetailVO.model_validate(p).id for p in page.data]
        assert post_id in post_ids
    finally:
        cleanup_post_and_tags(post_id, tag_id, category_id)
