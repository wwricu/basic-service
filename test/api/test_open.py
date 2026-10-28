import uuid

from fastapi import status

from test.api.utils import cleanup_post_and_tags, create_published_post, public_post_ids
from test.test_utils import client
from wwricu.domain.common import AboutPageVO, PageVO
from wwricu.domain.enum import TagTypeEnum
from wwricu.domain.post import PostPreviewVO, PostSearchVO
from wwricu.domain.tag import TagVO


def test_open_get_about():
    response = client.get('/open/about')
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(AboutPageVO.model_validate(response.json()).content, (str, type(None)))


def test_open_post_list_and_detail():
    post_id, tag_id, category_id = create_published_post()
    try:
        tags = [TagVO.model_validate(t) for t in client.get(f'/open/tags/{TagTypeEnum.POST_TAG}').json()]
        categories = [TagVO.model_validate(t) for t in client.get(f'/open/tags/{TagTypeEnum.POST_CAT}').json()]
        tag = next((t for t in tags if t.id == tag_id), None)
        category = next((c for c in categories if c.id == category_id), None)
        assert tag is not None and category is not None

        response = client.post(
            '/open/post/all',
            json={'page_index': 1, 'page_size': 10, 'tag_list': [tag.name], 'category': category.name}
        )
        assert response.status_code == status.HTTP_200_OK
        page = PageVO[PostPreviewVO].model_validate(response.json())
        assert (page.page_index, page.page_size) == (1, 10)
        assert post_id in [post.id for post in page.data]
        assert post_id in public_post_ids()
        assert client.get(f'/open/post/detail/{post_id}').status_code == status.HTTP_200_OK
    finally:
        cleanup_post_and_tags(post_id, tag_id, category_id)


def test_open_search_finds_indexed_post():
    keyword = f'Searchprobe{uuid.uuid4().hex[:8]}'
    post_id, tag_id, category_id = create_published_post(keyword)
    try:
        response = client.get('/open/post/search', params={'keyword': keyword})
        assert response.status_code == status.HTTP_200_OK
        assert post_id in [PostSearchVO.model_validate(hit).id for hit in response.json()]
    finally:
        cleanup_post_and_tags(post_id, tag_id, category_id)
