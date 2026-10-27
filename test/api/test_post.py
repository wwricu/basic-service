from fastapi import status

from test.api.utils import cleanup_post_and_tags, create_post, create_tag, public_post_ids
from test.test_utils import client
from wwricu.domain.common import PageVO
from wwricu.domain.enum import PostStatusEnum, TagTypeEnum
from wwricu.domain.post import PostDetailVO, PostPreviewVO


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
            'status': PostStatusEnum.PUBLISHED,
            'content': 'Lifecycle test content',
            'tag_id_list': [tag.id],
            'category_id': category.id
        })
        assert response.status_code == status.HTTP_200_OK
        detail = PostDetailVO.model_validate(response.json())
        assert [t.id for t in detail.tag_list] == [tag.id]
        assert detail.category is not None and detail.category.id == category.id
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
