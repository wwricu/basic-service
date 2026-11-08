import sqlite3
import uuid

from fastapi import status

from test.api.utils import cleanup_post_and_tags, create_post, create_published_post, create_tag, public_post_ids
from test.test_utils import client
from wwricu.component.tokenize import segment
from wwricu.config import app_config
from wwricu.domain.common import PageVO
from wwricu.domain.enum import ManageCommandEnum, PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostDetailVO, PostPreviewVO, PostSearchVO


def test_post_lifecycle():
    post = create_post()
    tag = create_tag(tag_type=TagTypeEnum.POST_TAG)
    category = create_tag(tag_type=TagTypeEnum.POST_CAT)
    try:
        assert post.status == PostStatusEnum.DRAFT
        admin_list = client.post('/admin/post/all', json={'status': PostStatusEnum.DRAFT, 'page_index': 1, 'page_size': 10})
        assert post.id in [p.id for p in PageVO[PostPreviewVO].model_validate(admin_list.json()).data]
        assert client.get(f'/open/post/detail/{post.id}').status_code == status.HTTP_404_NOT_FOUND

        response = client.post('/admin/post/update', json={
            'id': post.id,
            'title': 'Lifecycle Test Post',
            'preview': 'Lifecycle test preview',
            'content': 'Lifecycle test content',
            'tag_id_list': [tag.id],
            'category_id': category.id
        })
        assert response.status_code == status.HTTP_200_OK
        detail = PostDetailVO.model_validate(response.json())
        assert detail.status == PostStatusEnum.DRAFT
        assert [t.id for t in detail.tag_list] == [tag.id]
        assert detail.category is not None and detail.category.id == category.id

        assert client.post(f'/admin/post/status/{post.id}', json={'status': PostStatusEnum.PUBLISHED}).status_code == status.HTTP_200_OK
        assert post.id in public_post_ids()
        assert client.get(f'/open/post/detail/{post.id}').status_code == status.HTTP_200_OK

        # a published post has to be revoked before it can be trashed, exactly as the admin list offers it
        assert client.delete(f'/admin/post/delete/{post.id}').status_code == status.HTTP_403_FORBIDDEN

        assert client.post(f'/admin/post/status/{post.id}', json={'status': PostStatusEnum.DRAFT}).status_code == status.HTTP_200_OK
        assert post.id not in public_post_ids()
        assert client.get(f'/open/post/detail/{post.id}').status_code == status.HTTP_404_NOT_FOUND

        assert client.delete(f'/admin/post/delete/{post.id}').status_code == status.HTTP_200_OK
        assert client.get(f'/admin/post/detail/{post.id}').json() is None
    finally:
        cleanup_post_and_tags(post.id, tag.id, category.id)


def test_search_index_follows_post_status():
    keyword = f'Indexprobe{uuid.uuid4().hex[:8]}'
    draft = create_post()
    post_id, tag_id, category_id = create_published_post(keyword)
    try:
        response = client.post('/admin/post/update', json={
            'id': draft.id, 'title': keyword, 'preview': keyword, 'content': keyword, 'tag_id_list': []
        })
        assert response.status_code == status.HTTP_200_OK
        assert search_ids(keyword) == [post_id]

        assert client.post(f'/admin/post/status/{post_id}', json={'status': PostStatusEnum.DRAFT}).status_code == status.HTTP_200_OK
        assert search_ids(keyword) == []

        assert client.post(f'/admin/post/status/{post_id}', json={'status': PostStatusEnum.PUBLISHED}).status_code == status.HTTP_200_OK
        assert search_ids(keyword) == [post_id]
    finally:
        cleanup_post_and_tags(post_id, tag_id, category_id)
        client.delete(f'/admin/post/delete/{draft.id}')


def test_rebuild_search_index_clears_rows_the_write_path_left_behind():
    keyword = f'Rebuildprobe{uuid.uuid4().hex[:8]}'
    draft = create_post()
    trashed = create_post()
    assert client.delete(f'/admin/post/delete/{trashed.id}').status_code == status.HTTP_200_OK
    post_id, tag_id, category_id = create_published_post(keyword)
    try:
        # the draft really carries the keyword, so a rebuild that re-indexed drafts would leave it in the table
        assert client.post('/admin/post/update', json={
            'id': draft.id, 'title': keyword, 'preview': keyword, 'content': keyword, 'tag_id_list': []
        }).status_code == status.HTTP_200_OK
        assert search_ids(keyword) == [post_id]

        _plant_index(draft.id, keyword)
        _plant_index(trashed.id, keyword)
        # /open/post/search filters on post status, so leftover rows are only observable in the index table
        assert _index_rowids(keyword) == sorted([post_id, draft.id, trashed.id])

        assert client.post('/admin/manage/command', json={
            'command': ManageCommandEnum.REBUILD_SEARCH_INDEX, 'value': ''
        }).status_code == status.HTTP_200_OK
        assert _index_rowids(keyword) == [post_id]
        assert search_ids(keyword) == [post_id]
    finally:
        cleanup_post_and_tags(post_id, tag_id, category_id)
        client.delete(f'/admin/post/delete/{draft.id}')


def _plant_index(post_id: int, keyword: str):
    with sqlite3.connect(app_config.database.name) as conn:
        conn.execute(
            'insert into wwr_blog_post_search (rowid, title, preview, search_content) values (?, ?, ?, ?)',
            (post_id, segment(keyword), segment(keyword), segment(keyword))
        )


def _index_rowids(keyword: str) -> list[int]:
    with sqlite3.connect(app_config.database.name) as conn:
        return [row[0] for row in conn.execute(
            'select rowid from wwr_blog_post_search where title = ? order by rowid', (segment(keyword),)
        )]


def search_ids(keyword: str) -> list[int]:
    response = client.get('/open/post/search', params={'keyword': keyword})
    assert response.status_code == status.HTTP_200_OK
    return [PostSearchVO.model_validate(hit).id for hit in response.json()]
