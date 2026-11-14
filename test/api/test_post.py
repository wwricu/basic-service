import uuid

from fastapi import status

from test.api.utils import cleanup_post_and_tags, create_post, create_tag
from test.test_utils import client
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum


def test_post_lifecycle():
    keyword = f'Lifecycle{uuid.uuid4().hex[:8]}'
    post = create_post()
    tag = create_tag(TagTypeEnum.POST_TAG)
    category = create_tag(TagTypeEnum.POST_CAT)
    try:
        assert post.status == PostStatusEnum.DRAFT
        admin_list = client.post('/admin/post/all', json={'status': PostStatusEnum.DRAFT, 'page_index': 1, 'page_size': 10})
        assert post.id in [p['id'] for p in admin_list.json()['data']]
        assert client.get(f'/open/post/detail/{post.id}').status_code == status.HTTP_404_NOT_FOUND

        response = client.post('/admin/post/update', json={
            'id': post.id,
            'title': keyword,
            'preview': keyword,
            'content': keyword,
            'tag_id_list': [tag.id],
            'category_id': category.id
        })
        assert response.status_code == status.HTTP_200_OK
        detail = response.json()
        assert [t['id'] for t in detail['tag_list']] == [tag.id]
        assert detail['category']['id'] == category.id

        assert client.post(f'/admin/post/status/{post.id}', json={'status': PostStatusEnum.PUBLISHED}).status_code == status.HTTP_200_OK
        assert client.get(f'/open/post/detail/{post.id}').status_code == status.HTTP_200_OK
        search = client.get('/open/post/search', params={'keyword': keyword})
        assert search.status_code == status.HTTP_200_OK and [hit['id'] for hit in search.json()] == [post.id]

        assert client.get('/open/about').status_code == status.HTTP_200_OK
        assert tag.id in [t['id'] for t in client.get(f'/open/tags/{TagTypeEnum.POST_TAG}').json()]
        assert category.id in [t['id'] for t in client.get(f'/open/tags/{TagTypeEnum.POST_CAT}').json()]
        filtered = client.post('/open/post/all', json={'page_index': 1, 'page_size': 10, 'tag_list': [tag.name], 'category': category.name})
        assert filtered.status_code == status.HTTP_200_OK and post.id in [p['id'] for p in filtered.json()['data']]
        assert tag.id in [t['id'] for t in client.post('/admin/tag/all', json={'type': TagTypeEnum.POST_TAG}).json()]
        new_name = f'{tag.name}_renamed'
        assert client.post('/admin/tag/update', json={'id': tag.id, 'name': new_name, 'type': TagTypeEnum.POST_TAG}).status_code == status.HTTP_200_OK
        assert new_name in [t['name'] for t in client.post('/admin/tag/all', json={'type': TagTypeEnum.POST_TAG}).json()]

        # a published post has to be revoked before it can be trashed, exactly as the admin list offers it
        assert client.delete(f'/admin/post/delete/{post.id}').status_code == status.HTTP_403_FORBIDDEN

        assert client.post(f'/admin/post/status/{post.id}', json={'status': PostStatusEnum.DRAFT}).status_code == status.HTTP_200_OK
        assert post.id not in [p['id'] for p in client.post('/open/post/all', json={'page_index': 1, 'page_size': 10}).json()['data']]
        assert client.get(f'/open/post/detail/{post.id}').status_code == status.HTTP_404_NOT_FOUND

        assert client.delete(f'/admin/post/delete/{post.id}').status_code == status.HTTP_200_OK
        assert client.get(f'/admin/post/detail/{post.id}').json() is None
    finally:
        cleanup_post_and_tags(post.id, tag.id, category.id)
