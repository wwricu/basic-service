import sqlite3

import pyotp
from fastapi import status

from test.api.utils import create_post_and_delete
from test.test_utils import client
from wwricu.config import app_config
from wwricu.domain.common import TrashBinVO
from wwricu.domain.constant import HttpErrorDetail
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

    client.delete(f'/admin/post/delete/{post_id}')
    hard_delete = client.post('/admin/manage/trash/edit', json={'id': post_id, 'type': EntityTypeEnum.BLOG_POST, 'delete': True})
    assert hard_delete.status_code == status.HTTP_200_OK
    assert client.get(f'/admin/post/detail/{post_id}').json() is None
    assert post_id not in _trashed_post_ids()


def _trashed_post_ids() -> list[int]:
    response = client.get('/admin/manage/trash/all')
    assert response.status_code == status.HTTP_200_OK
    return [item.id for item in map(TrashBinVO.model_validate, response.json()) if item.type == EntityTypeEnum.BLOG_POST]


def test_config_set_refuses_a_key_without_a_write_rule():
    _clear_totp()
    response = client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.TOTP_SECRET, 'value': 'leak'})
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    assert ConfigKeyEnum.TOTP_SECRET not in _config_keys()


def test_config_set_refuses_a_non_null_totp_enforce():
    _clear_totp()
    response = client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.TOTP_ENFORCE, 'value': '1'})
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE
    assert ConfigKeyEnum.TOTP_ENFORCE not in _config_keys()


def test_a_null_username_deletes_both_login_rows():
    for key, value in ((ConfigKeyEnum.USERNAME, 'aggregate_user'), (ConfigKeyEnum.PASSWORD, 'Aggregate#12345')):
        assert client.post('/admin/manage/config/set', json={'key': key, 'value': value}).status_code == status.HTTP_200_OK
    assert {ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} <= _config_keys()

    reset = client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.USERNAME, 'value': None})
    assert reset.status_code == status.HTTP_200_OK
    # only the username was nulled, and the password row went with it in the same statement
    assert not ({ConfigKeyEnum.USERNAME, ConfigKeyEnum.PASSWORD} & _config_keys())


def test_a_null_totp_enforce_deletes_the_secret_too():
    assert len(client.post('/admin/manage/totp/enroll').json()) == 32
    assert ConfigKeyEnum.TOTP_SECRET in _config_keys()

    disable = client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.TOTP_ENFORCE, 'value': None})
    assert disable.status_code == status.HTTP_200_OK
    assert not ({ConfigKeyEnum.TOTP_ENFORCE, ConfigKeyEnum.TOTP_SECRET} & _config_keys())


def test_a_wrong_totp_code_is_a_bad_request():
    secret = client.post('/admin/manage/totp/enroll').json()
    wrong = (int(pyotp.TOTP(secret).now()) + 1) % 1000000
    response = client.post('/admin/manage/totp/confirm', json={'totp': f'{wrong:06d}'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['detail'] == HttpErrorDetail.WRONG_TOTP

    assert client.post('/admin/manage/totp/confirm', json={'totp': pyotp.TOTP(secret).now()}).status_code == status.HTTP_200_OK
    assert client.get(f'/admin/manage/config/get?key={ConfigKeyEnum.TOTP_ENFORCE}').json().isdigit()
    client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.TOTP_ENFORCE, 'value': None})


def test_a_legacy_true_row_still_enforces_totp():
    # Rows written before the timestamp format hold "True"; the readers test `is not None`, so an
    # old row has to keep enforcing without a migration.
    client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.USERNAME, 'value': 'legacy_user'})
    client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.PASSWORD, 'value': 'Legacy#12345'})
    _seed_config(ConfigKeyEnum.TOTP_ENFORCE, 'True')
    try:
        response = client.post('/admin/login', json={'username': 'legacy_user', 'password': 'Legacy#12345'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()['detail'] == HttpErrorDetail.NEED_TOTP
    finally:
        client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.USERNAME, 'value': None})
        client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.TOTP_ENFORCE, 'value': None})


def _clear_totp():
    # The aggregate delete is the only way to drop a secret, and it leaves the assertions independent
    # of whatever a previous run left behind.
    client.post('/admin/manage/config/set', json={'key': ConfigKeyEnum.TOTP_ENFORCE, 'value': None})


def _config_keys() -> set[ConfigKeyEnum]:
    with sqlite3.connect(app_config.database.name) as conn:
        return {row[0] for row in conn.execute('select key from wwr_sys_config where deleted = 0')}


def _seed_config(key: ConfigKeyEnum, value: str):
    # Bypasses the api on purpose: no endpoint may write this value any more.
    with sqlite3.connect(app_config.database.name) as conn:
        conn.execute(
            'insert into wwr_sys_config (key, value, deleted) values (?, ?, 0) on conflict (key) do update set value = ?, deleted = 0',
            (key, value, value)
        )
