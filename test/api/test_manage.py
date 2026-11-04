import sqlite3

import pyotp
from fastapi import status

from test.api.utils import create_post_and_delete
from test.test_utils import client
from wwricu.config import app_config
from wwricu.domain.common import TrashBinVO
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import ConfigKeyEnum, EntityTypeEnum, ManageCommandEnum


def test_command_set_and_get():
    about = f'/admin/manage/config/get?key={ConfigKeyEnum.ABOUT_CONTENT}'
    original = client.get(about).json()
    try:
        assert _command(ManageCommandEnum.SET_ABOUT, 'test about content').status_code == status.HTTP_200_OK
        assert client.get(about).json() == 'test about content'
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


def test_a_command_outside_the_enum_is_refused():
    _clear_totp()
    response = client.post('/admin/manage/command', json={'command': 'set_totp_secret', 'value': 'leak'})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert not ({ConfigKeyEnum.TOTP_SECRET, ConfigKeyEnum.TOTP_ENFORCE} & _config_keys())


def test_reset_login_deletes_both_rows():
    assert _command(ManageCommandEnum.SET_USERNAME, 'command_user').status_code == status.HTTP_200_OK
    assert _command(ManageCommandEnum.SET_PASSWORD, 'Command#12345').status_code == status.HTTP_200_OK
    assert {ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} <= _config_keys()

    assert _command(ManageCommandEnum.RESET_LOGIN).status_code == status.HTTP_200_OK
    assert not ({ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} & _config_keys())


def test_disable_totp_deletes_the_secret_too():
    assert len(_command(ManageCommandEnum.ENROLL_TOTP).json()) == 32
    assert ConfigKeyEnum.TOTP_SECRET in _config_keys()

    assert _command(ManageCommandEnum.DISABLE_TOTP).status_code == status.HTTP_200_OK
    assert not ({ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET} & _config_keys())


def test_a_wrong_totp_code_is_a_bad_request():
    secret = _command(ManageCommandEnum.ENROLL_TOTP).json()
    wrong = (int(pyotp.TOTP(secret).now()) + 1) % 1000000
    response = _command(ManageCommandEnum.CONFIRM_TOTP, f'{wrong:06d}')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == HttpErrorDetail.WRONG_TOTP

    assert _command(ManageCommandEnum.CONFIRM_TOTP, pyotp.TOTP(secret).now()).status_code == status.HTTP_200_OK
    assert client.get(f'/admin/manage/config/get?key={ConfigKeyEnum.TOTP_ENFORCE}').json().isdigit()
    _command(ManageCommandEnum.DISABLE_TOTP)


def test_a_legacy_true_row_still_enforces_totp():
    _command(ManageCommandEnum.SET_USERNAME, 'legacy_user')
    _command(ManageCommandEnum.SET_PASSWORD, 'Legacy#12345')
    _seed_config(ConfigKeyEnum.TOTP_ENFORCE, 'True')
    try:
        response = client.post('/admin/login', json={'username': 'legacy_user', 'password': 'Legacy#12345'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()['detail'] == HttpErrorDetail.NEED_TOTP
    finally:
        _command(ManageCommandEnum.RESET_LOGIN)
        _command(ManageCommandEnum.DISABLE_TOTP)


def _clear_totp():
    _command(ManageCommandEnum.DISABLE_TOTP)


def _command(command: ManageCommandEnum, value: str = ''):
    return client.post('/admin/manage/command', json={'command': command, 'value': value})


def _config_keys() -> set[ConfigKeyEnum]:
    with sqlite3.connect(app_config.database.name) as conn:
        return {row[0] for row in conn.execute('select key from wwr_sys_config where deleted = 0')}


def _seed_config(key: ConfigKeyEnum, value: str):
    with sqlite3.connect(app_config.database.name) as conn:
        conn.execute(
            'insert into wwr_sys_config (key, value, deleted) values (?, ?, 0) on conflict (key) do update set value = ?, deleted = 0',
            (key, value, value)
        )
