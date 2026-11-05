import json
import sqlite3

import pyotp
import pytest
from fastapi import status

from test.api.utils import create_post_and_delete
from test.test_utils import client
from wwricu.config import app_config
from wwricu.database import conf_db
from wwricu.domain.common import TrashBinVO
from wwricu.domain.constant import HttpErrorDetail
from wwricu.domain.enum import ConfigKeyEnum, EntityTypeEnum, ManageCommandEnum


def test_command_set_and_get():
    original = _read(ConfigKeyEnum.ABOUT_CONTENT).json()
    try:
        assert _command(ManageCommandEnum.SET_ABOUT, 'test about content').status_code == status.HTTP_200_OK
        assert _read(ConfigKeyEnum.ABOUT_CONTENT).json() == 'test about content'
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


def test_a_read_outside_the_whitelist_is_refused():
    assert _read(ConfigKeyEnum.PASSWORD).status_code == status.HTTP_403_FORBIDDEN
    assert _read(ConfigKeyEnum.TOTP_SECRET).status_code == status.HTTP_403_FORBIDDEN
    assert client.get('/admin/manage/config/get?key=not_a_config_key').status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_set_login_overwrites_and_reset_clears_both_rows():
    assert _command(ManageCommandEnum.SET_LOGIN, _login('command_user', 'Command#12345')).status_code == status.HTTP_200_OK
    assert _read(ConfigKeyEnum.USERNAME).json() == 'command_user'
    assert {ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} <= _config_keys()
    assert client.post('/admin/login', json={'username': 'command_user', 'password': 'Command#12345'}).status_code == status.HTTP_200_OK

    assert _command(ManageCommandEnum.SET_LOGIN, _login('second_user', 'Second#12345')).status_code == status.HTTP_200_OK
    assert _read(ConfigKeyEnum.USERNAME).json() == 'second_user'

    assert _command(ManageCommandEnum.RESET_LOGIN).status_code == status.HTTP_200_OK
    assert not ({ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} & _config_keys())


def test_an_invalid_credential_is_a_bad_request():
    for username, password, detail in (('ab', 'Valid#12345', 'Invalid username'),
                                       ('1nvalid', 'Valid#12345', 'Invalid username'),
                                       ('valid_user', 'short', 'Invalid password'),
                                       ('valid_user', 'AlphanumericOnly', 'Invalid password')):
        response = _command(ManageCommandEnum.SET_LOGIN, _login(username, password))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['detail'] == detail
    assert not ({ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} & _config_keys())


def test_a_login_that_is_not_a_credential_pair_is_a_bad_request():
    response = _command(ManageCommandEnum.SET_LOGIN, 'command_user')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not ({ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} & _config_keys())


def test_a_failed_password_write_rolls_back_the_username(monkeypatch):
    original = conf_db.upsert

    async def fail_on_password(key, value):
        if key == ConfigKeyEnum.PASSWORD:
            raise RuntimeError('write failed')
        await original(key, value)

    monkeypatch.setattr(conf_db, 'upsert', fail_on_password)
    with pytest.raises(RuntimeError):
        _command(ManageCommandEnum.SET_LOGIN, _login('rollback_user', 'Rollback#12345'))
    assert ConfigKeyEnum.USERNAME not in _config_keys()


def test_disable_totp_deletes_the_secret_too():
    assert len(_command(ManageCommandEnum.ENROLL_TOTP).json()) == 32
    assert ConfigKeyEnum.TOTP_SECRET in _config_keys()

    assert _command(ManageCommandEnum.DISABLE_TOTP).status_code == status.HTTP_200_OK
    assert not ({ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET} & _config_keys())
    assert _read(ConfigKeyEnum.TOTP_ENFORCE).json() is None


def test_a_wrong_totp_code_is_a_bad_request():
    secret = _command(ManageCommandEnum.ENROLL_TOTP).json()
    wrong = (int(pyotp.TOTP(secret).now()) + 1) % 1000000
    response = _command(ManageCommandEnum.CONFIRM_TOTP, f'{wrong:06d}')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == HttpErrorDetail.WRONG_TOTP

    assert _command(ManageCommandEnum.CONFIRM_TOTP, pyotp.TOTP(secret).now()).status_code == status.HTTP_200_OK
    assert _read(ConfigKeyEnum.TOTP_ENFORCE).json() is not None
    _command(ManageCommandEnum.DISABLE_TOTP)


def test_a_legacy_true_row_still_enforces_totp():
    _command(ManageCommandEnum.SET_LOGIN, _login('legacy_user', 'Legacy#12345'))
    _seed_config(ConfigKeyEnum.TOTP_ENFORCE, 'True')
    try:
        response = client.post('/admin/login', json={'username': 'legacy_user', 'password': 'Legacy#12345'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()['detail'] == HttpErrorDetail.NEED_TOTP
        assert _read(ConfigKeyEnum.TOTP_ENFORCE).json() == 'True'
    finally:
        _command(ManageCommandEnum.RESET_LOGIN)
        _command(ManageCommandEnum.DISABLE_TOTP)


def _read(key: ConfigKeyEnum):
    return client.get(f'/admin/manage/config/get?key={key}')


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


def _login(username: str, password: str) -> str:
    return json.dumps({'username': username, 'password': password})
