from fastapi import status
from loguru import logger as log

from test.api.utils import create_post_and_delete
from test.test_utils import client
from wwricu.domain.common import TrashBinVO
from wwricu.domain.enum import ConfigKeyEnum, EntityTypeEnum


def test_config_set_and_get():
    set_response = client.post('/manage/config/set', json={'key': ConfigKeyEnum.ABOUT_CONTENT, 'value': 'test about content'})
    assert set_response.status_code == status.HTTP_200_OK
    get_response = client.get(f'/manage/config/get?key={ConfigKeyEnum.ABOUT_CONTENT}')
    log.info(get_response.json())
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json() == 'test about content'


def test_trash_recover_post():
    post_id = create_post_and_delete()
    trash_response = client.get('/manage/trash/all')
    assert trash_response.status_code == status.HTTP_200_OK
    trash_items = [TrashBinVO.model_validate(item) for item in trash_response.json()]
    assert any(item.id == post_id and item.type == EntityTypeEnum.BLOG_POST for item in trash_items)

    recover_data = {'id': post_id, 'type': EntityTypeEnum.BLOG_POST, 'delete': False}
    edit_response = client.post('/manage/trash/edit', json=recover_data)
    assert edit_response.status_code == status.HTTP_200_OK

    detail_response = client.get(f'/post/detail/{post_id}')
    assert detail_response.status_code == status.HTTP_200_OK
    assert detail_response.json() is not None

    client.get(f'/post/delete/{post_id}')


def test_trash_hard_delete_post():
    post_id = create_post_and_delete()
    hard_delete_data = {'id': post_id, 'type': EntityTypeEnum.BLOG_POST, 'delete': True}
    edit_response = client.post('/manage/trash/edit', json=hard_delete_data)
    assert edit_response.status_code == status.HTTP_200_OK

    trash_response = client.get('/manage/trash/all')
    trash_items = [TrashBinVO.model_validate(item) for item in trash_response.json()]
    assert not any(item.id == post_id and item.type == EntityTypeEnum.BLOG_POST for item in trash_items)
