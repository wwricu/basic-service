from fastapi import status

from test.api.utils import create_post_and_delete
from test.test_utils import client
from wwricu.domain.common import TrashBinVO
from wwricu.domain.enum import ConfigKeyEnum, EntityTypeEnum


def test_config_set_and_get():
    about = f'/admin/manage/config/get?key={ConfigKeyEnum.ABOUT_CONTENT}'
    original = client.get(about).json()
    try:
        set_response = client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.ABOUT_CONTENT, 'value': 'test about content'})
        assert set_response.status_code == status.HTTP_200_OK
        get_response = client.get(about)
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.json() == 'test about content'
    finally:
        client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.ABOUT_CONTENT, 'value': original})


def test_trash_recover_and_hard_delete():
    post_id = create_post_and_delete()
    assert post_id in _trashed_post_ids()

    # recover pulls it out of the trash, which is also what takes it out of reach of a later hard delete
    recover = client.post('/admin/manage/trash/edit', json={'id': post_id, 'type': EntityTypeEnum.BLOG_POST, 'delete': False})
    assert recover.status_code == status.HTTP_200_OK
    assert client.get(f'/admin/post/detail/{post_id}').json() is not None
    assert post_id not in _trashed_post_ids()

    client.get(f'/admin/post/delete/{post_id}')
    hard_delete = client.post('/admin/manage/trash/edit', json={'id': post_id, 'type': EntityTypeEnum.BLOG_POST, 'delete': True})
    assert hard_delete.status_code == status.HTTP_200_OK
    assert client.get(f'/admin/post/detail/{post_id}').json() is None
    assert post_id not in _trashed_post_ids()


def _trashed_post_ids() -> list[int]:
    response = client.get('/admin/manage/trash/all')
    assert response.status_code == status.HTTP_200_OK
    return [item.id for item in map(TrashBinVO.model_validate, response.json()) if item.type == EntityTypeEnum.BLOG_POST]
