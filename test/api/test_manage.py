import json
import sqlite3

import pyotp
from fastapi import status

from test.api.utils import create_post_and_delete
from test.test_utils import client
from wwricu.config import app_config
from wwricu.domain.common import TrashBinVO
from wwricu.domain.enum import ConfigKeyEnum, EntityTypeEnum, ManageCommandEnum


def test_command_set_and_get():
    original = _read(ConfigKeyEnum.ABOUT_CONTENT).json()
    try:
        assert _command(ManageCommandEnum.SET_ABOUT, 'test about content').status_code == status.HTTP_200_OK
        assert _read(ConfigKeyEnum.ABOUT_CONTENT).json() == 'test about content'
        assert _read(ConfigKeyEnum.PASSWORD).status_code == status.HTTP_403_FORBIDDEN
    finally:
        _command(ManageCommandEnum.SET_ABOUT, original)


def test_trash_recover_and_hard_delete():
    post_id = create_post_and_delete()
    assert post_id in _trashed_post_ids()

    # recover pulls it out of the trash, which is also what takes it out of reach of a later hard delete
    recover = client.post('/admin/manage/trash/edit', json={'id': post_id, 'type': EntityTypeEnum.BLOG_POST, 'delete': False})
    assert recover.status_code == status.HTTP_200_OK
    assert client.get(f'/admin/post/detail/{post_id}').json() is not None
    assert post_id not in _trashed_post_ids()

    client.delete(f'/admin/post/delete/{post_id}')
    hard_delete = client.post('/admin/manage/trash/edit', json={'id': post_id, 'type': EntityTypeEnum.BLOG_POST, 'delete': True})
    assert hard_delete.status_code == status.HTTP_200_OK
    assert client.get(f'/admin/post/detail/{post_id}').json() is None
    assert post_id not in _trashed_post_ids()


def _trashed_post_ids() -> list[int]:
    response = client.get('/admin/manage/trash/all')
    assert response.status_code == status.HTTP_200_OK
    return [item.id for item in map(TrashBinVO.model_validate, response.json()) if item.type == EntityTypeEnum.BLOG_POST]


def test_set_login_overwrites_and_reset_clears_both_rows():
    assert _command(ManageCommandEnum.SET_LOGIN, _login('command_user', 'Command#12345')).status_code == status.HTTP_200_OK
    assert _read(ConfigKeyEnum.USERNAME).json() == 'command_user'
    assert {ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} <= _config_keys()
    assert client.post('/admin/login', json={'username': 'command_user', 'password': 'Command#12345'}).status_code == status.HTTP_200_OK

    assert _command(ManageCommandEnum.SET_LOGIN, _login('second_user', 'Second#12345')).status_code == status.HTTP_200_OK
    assert _read(ConfigKeyEnum.USERNAME).json() == 'second_user'

    assert _command(ManageCommandEnum.RESET_LOGIN).status_code == status.HTTP_200_OK
    assert not ({ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} & _config_keys())


def test_totp_enroll_confirm_and_disable():
    secret = _command(ManageCommandEnum.ENROLL_TOTP).json()
    assert len(secret) == 32
    assert ConfigKeyEnum.TOTP_SECRET in _config_keys()

    assert _command(ManageCommandEnum.CONFIRM_TOTP, pyotp.TOTP(secret).now()).status_code == status.HTTP_200_OK
    assert _read(ConfigKeyEnum.TOTP_ENFORCE).json() is not None

    assert _command(ManageCommandEnum.DISABLE_TOTP).status_code == status.HTTP_200_OK
    assert not ({ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET} & _config_keys())


def _read(key: ConfigKeyEnum):
    return client.get(f'/admin/manage/config/get?key={key}')


def _command(command: ManageCommandEnum, value: str = ''):
    return client.post('/admin/manage/command', json={'command': command, 'value': value})


def _config_keys() -> set[ConfigKeyEnum]:
    with sqlite3.connect(app_config.database.name) as conn:
        return {row[0] for row in conn.execute('select key from wwr_sys_config where deleted = 0')}


def _login(username: str, password: str) -> str:
    return json.dumps({'username': username, 'password': password})
