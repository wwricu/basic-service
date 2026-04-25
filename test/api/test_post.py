import io
import uuid

from fastapi import status
from loguru import logger as log

from test.api.utils import create_post
from test.test_utils import client
from wwricu.domain.common import PageVO
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostDetailVO
from wwricu.domain.tag import TagVO


def test_create_post():
    post = create_post()
    log.info(f'Created post: {post.id}')
    try:
        assert post.id is not None
        assert post.status == PostStatusEnum.DRAFT
    finally:
        client.get(f'/post/delete/{post.id}')


def test_get_all_posts_with_status_filter():
    response = client.post('/post/all', json={'status': PostStatusEnum.DRAFT})
    assert response.status_code == status.HTTP_200_OK
    page = PageVO[PostDetailVO].model_validate(response.json())
    for post_data in page.data:
        post = PostDetailVO.model_validate(post_data)
        assert post.status == PostStatusEnum.DRAFT


def test_get_all_posts_with_deleted_filter():
    post = create_post()
    try:
        client.get(f'/post/delete/{post.id}')
        response = client.post('/post/all', json={'deleted': True})
        assert response.status_code == status.HTTP_200_OK
        page = PageVO[PostDetailVO].model_validate(response.json())
        deleted_ids = [PostDetailVO.model_validate(p).id for p in page.data]
        assert post.id in deleted_ids
    finally:
        pass


def test_get_post_detail():
    post = create_post()
    try:
        response = client.get(f'/post/detail/{post.id}')
        log.info(response.json())
        assert response.status_code == status.HTTP_200_OK
        detail = PostDetailVO.model_validate(response.json())
        assert detail.id == post.id
    finally:
        client.get(f'/post/delete/{post.id}')


def test_get_deleted_post_detail():
    post = create_post()
    client.get(f'/post/delete/{post.id}')
    response = client.get(f'/post/detail/{post.id}')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is None


def test_update_post_with_tags_and_category():
    post = create_post()
    tag_response = client.post('/tag/create', json={'name': f'update_test_{uuid.uuid4().hex[:8]}', 'type': TagTypeEnum.POST_TAG})
    tag = TagVO.model_validate(tag_response.json())
    cat_response = client.post('/tag/create', json={'name': f'update_cat_{uuid.uuid4().hex[:8]}', 'type': TagTypeEnum.POST_CAT})
    category = TagVO.model_validate(cat_response.json())
    try:
        update_data = {
            'id': post.id,
            'title': 'Post With Tags',
            'preview': 'Preview with tags',
            'status': PostStatusEnum.PUBLISHED,
            'content': 'Content with tags and category',
            'tag_id_list': [tag.id],
            'category_id': category.id
        }
        response = client.post('/post/update', json=update_data)
        assert response.status_code == status.HTTP_200_OK
        detail_response = client.get(f'/post/detail/{post.id}')
        updated = PostDetailVO.model_validate(detail_response.json())
        assert updated.title == 'Post With Tags'
        assert len(updated.tag_list) == 1
        assert updated.tag_list[0].id == tag.id
        assert updated.category is not None
        assert updated.category.id == category.id
    finally:
        client.get(f'/post/delete/{post.id}')
        client.get(f'/tag/delete/{tag.id}')
        client.get(f'/tag/delete/{category.id}')


def test_update_post_not_found():
    update_data = {
        'id': 99999,
        'title': 'Not Found',
        'preview': 'preview',
        'status': PostStatusEnum.DRAFT,
        'content': 'content',
        'tag_id_list': []
    }
    response = client.post('/post/update', json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_post_status():
    post = create_post()
    try:
        assert post.status == PostStatusEnum.DRAFT
        response = client.get(f'/post/status/{post.id}?status=published')
        log.info(response.json())
        assert response.status_code == status.HTTP_200_OK
        detail_response = client.get(f'/post/detail/{post.id}')
        updated = PostDetailVO.model_validate(detail_response.json())
        assert updated.status == PostStatusEnum.PUBLISHED

        response = client.get(f'/post/status/{post.id}?status=draft')
        assert response.status_code == status.HTTP_200_OK
        detail_response = client.get(f'/post/detail/{post.id}')
        updated = PostDetailVO.model_validate(detail_response.json())
        assert updated.status == PostStatusEnum.DRAFT
    finally:
        client.get(f'/post/delete/{post.id}')


def test_delete_post():
    post = create_post()
    delete_response = client.get(f'/post/delete/{post.id}')
    assert delete_response.status_code == status.HTTP_200_OK
    list_response = client.post('/post/all', json={'deleted': False})
    page = PageVO[PostDetailVO].model_validate(list_response.json())
    active_ids = [PostDetailVO.model_validate(p).id for p in page.data]
    assert post.id not in active_ids


def test_post_lifecycle():
    post = create_post()
    tag_response = client.post('/tag/create', json={'name': f'lifecycle_tag_{uuid.uuid4().hex[:8]}', 'type': TagTypeEnum.POST_TAG})
    tag = TagVO.model_validate(tag_response.json())
    cat_response = client.post('/tag/create', json={'name': f'lifecycle_cat_{uuid.uuid4().hex[:8]}', 'type': TagTypeEnum.POST_CAT})
    category = TagVO.model_validate(cat_response.json())
    try:
        assert post.status == PostStatusEnum.DRAFT

        detail_response = client.get(f'/post/detail/{post.id}')
        assert detail_response.status_code == status.HTTP_200_OK

        open_response = client.get(f'/open/post/detail/{post.id}')
        assert open_response.status_code == status.HTTP_404_NOT_FOUND

        update_data = {
            'id': post.id,
            'title': 'Lifecycle Test Post',
            'preview': 'Lifecycle test preview',
            'status': PostStatusEnum.PUBLISHED,
            'content': 'Lifecycle test content',
            'tag_id_list': [tag.id],
            'category_id': category.id
        }
        update_response = client.post('/post/update', json=update_data)
        assert update_response.status_code == status.HTTP_200_OK

        open_response = client.post('/open/post/all', json={})
        assert open_response.status_code == status.HTTP_200_OK
        page = PageVO[PostDetailVO].model_validate(open_response.json())
        post_ids = [PostDetailVO.model_validate(p).id for p in page.data]
        assert post.id in post_ids

        open_detail = client.get(f'/open/post/detail/{post.id}')
        assert open_detail.status_code == status.HTTP_200_OK

        client.get(f'/post/delete/{post.id}')

        open_response = client.post('/open/post/all', json={})
        page = PageVO[PostDetailVO].model_validate(open_response.json())
        post_ids = [PostDetailVO.model_validate(p).id for p in page.data]
        assert post.id not in post_ids

        detail_response = client.get(f'/post/detail/{post.id}')
        assert detail_response.json() is None
    finally:
        client.get(f'/post/delete/{post.id}')
        client.get(f'/tag/delete/{tag.id}')
        client.get(f'/tag/delete/{category.id}')


def test_upload_file():
    post = create_post()
    try:
        file_content = b'test file content for upload'
        file_obj = io.BytesIO(file_content)
        response = client.post(
            '/post/upload',
            files={'file': ('test_upload.txt', file_obj, 'text/plain')},
            data={'post_id': str(post.id), 'file_type': 'common'}
        )
        log.info(response.json())
        assert response.status_code == status.HTTP_200_OK
    finally:
        client.get(f'/post/delete/{post.id}')
