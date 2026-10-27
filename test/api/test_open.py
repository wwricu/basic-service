import contextlib
import sqlite3

import pytest
from fastapi import status
from loguru import logger as log

from test.api.utils import cleanup_post_and_tags, create_published_post_with_tag
from test.test_utils import client
from wwricu.component.tokenize import tokens
from wwricu.config import app_config
from wwricu.domain.common import AboutPageVO, PageVO
from wwricu.domain.enum import TagTypeEnum
from wwricu.domain.post import PostDetailVO, PostPreviewVO, PostSearchVO
from wwricu.domain.tag import TagVO


def test_open_get_about():
    response = client.get('/open/about')
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    about = AboutPageVO.model_validate(response.json())
    assert isinstance(about.content, (str, type(None)))


def test_open_get_posts():
    response = client.post('/open/post/all', json={'page_index': 1, 'page_size': 10})
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    page = PageVO.model_validate(response.json())
    for post in page.data:
        PostPreviewVO.model_validate(post)


def test_open_get_posts_pagination():
    response = client.post('/open/post/all', json={'page_index': 1, 'page_size': 5})
    assert response.status_code == status.HTTP_200_OK
    page = PageVO[PostPreviewVO].model_validate(response.json())
    assert page.page_index == 1
    assert page.page_size == 5
    assert page.count >= 0


def test_open_get_post_detail_not_found():
    response = client.get('/open/post/detail/99999')
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_open_get_post_detail_draft_not_found():
    create_response = client.get('/admin/post/create')
    post = PostDetailVO.model_validate(create_response.json())
    try:
        response = client.get(f'/open/post/detail/{post.id}')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    finally:
        client.get(f'/admin/post/delete/{post.id}')


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
        response = client.post('/open/post/all', json={'tag_list': [test_tag.name], 'page_index': 1, 'page_size': 10})
        assert response.status_code == status.HTTP_200_OK
        page = PageVO[PostPreviewVO].model_validate(response.json())
        post_ids = [PostPreviewVO.model_validate(p).id for p in page.data]
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
        response = client.post('/open/post/all', json={'category': test_cat.name, 'page_index': 1, 'page_size': 10})
        assert response.status_code == status.HTTP_200_OK
        page = PageVO[PostPreviewVO].model_validate(response.json())
        post_ids = [PostPreviewVO.model_validate(p).id for p in page.data]
        assert post_id in post_ids
    finally:
        cleanup_post_and_tags(post_id, tag_id, category_id)


def test_open_search_finds_existing_post():
    # Probe with a post already in the database so the assertion covers the whole join and
    # the run leaves no published post behind (the delete endpoint rejects published ones).
    response = client.post('/open/post/all', json={'page_index': 1, 'page_size': 10})
    assert response.status_code == status.HTTP_200_OK
    posts = PageVO[PostPreviewVO].model_validate(response.json()).data
    for post in posts:
        if terms := [t for t in tokens(post.title) if len(t) > 2]:
            response = client.get('/open/post/search', params={'keyword': max(terms, key=len)})
            assert response.status_code == status.HTTP_200_OK
            assert post.id in [PostSearchVO.model_validate(hit).id for hit in response.json()], \
                f'post {post.id} titled {post.title!r} is not reachable through search'
            return
    pytest.skip('no published post with an indexable title to probe')


def test_search_index_is_keyed_by_post_id():
    # Every live post must be reachable through rowid == post id, and no index row may point at a missing post.
    # A database still on the old fts5(id, ...) schema fails this: its rows carry an auto rowid and a separate id column.
    with contextlib.closing(sqlite3.connect(app_config.database.name)) as connection:
        columns = [row[1] for row in connection.execute('pragma table_info(wwr_blog_post_search)')]
        assert columns == ['title', 'preview', 'search_content']
        missing = connection.execute(
            'select count(*) from wwr_blog_post p where p.deleted = 0 and not exists'
            ' (select 1 from wwr_blog_post_search s where s.rowid = p.id)').fetchone()[0]
        assert missing == 0
        orphan = connection.execute(
            'select count(*) from wwr_blog_post_search s where not exists'
            ' (select 1 from wwr_blog_post p where p.id = s.rowid)').fetchone()[0]
        assert orphan == 0


def test_open_search_does_not_match_existing_post_id():
    response = client.post('/open/post/all', json={'page_index': 1, 'page_size': 1})
    assert response.status_code == status.HTTP_200_OK
    posts = PageVO[PostPreviewVO].model_validate(response.json()).data
    if not posts:
        pytest.skip('no published post to probe')
    response = client.get('/open/post/search', params={'keyword': str(posts[0].id)})
    assert response.status_code == status.HTTP_200_OK
    assert posts[0].id not in [PostSearchVO.model_validate(hit).id for hit in response.json()]
