import uuid

import pyotp
from fastapi import status
from loguru import logger as log

from test.test_utils import client
from test.api.test_common import _cleanup_login_lock, _reset_credentials
from wwricu.domain.common import TrashBinRO, TrashBinVO
from wwricu.domain.enum import ConfigKeyEnum, DatabaseActionEnum, EntityTypeEnum, TagTypeEnum
from wwricu.domain.post import PostDetailVO
from wwricu.domain.tag import TagVO


def _create_post_and_delete() -> int:
    create_response = client.get('/post/create')
    post = PostDetailVO.model_validate(create_response.json())
    client.get(f'/post/delete/{post.id}')
    return post.id


def _create_tag_and_delete() -> int:
    tag_response = client.post('/tag/create', json={'name': f'trash_test_{uuid.uuid4().hex[:8]}', 'type': TagTypeEnum.POST_TAG})
    tag = TagVO.model_validate(tag_response.json())
    client.get(f'/tag/delete/{tag.id}')
    return tag.id


def test_config_set_and_get():
    set_response = client.post('/manage/config/set', json={'key': ConfigKeyEnum.ABOUT_CONTENT, 'value': 'test about content'})
    assert set_response.status_code == status.HTTP_200_OK
    get_response = client.get(f'/manage/config/get?key={ConfigKeyEnum.ABOUT_CONTENT}')
    log.info(get_response.json())
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json() == 'test about content'


def test_config_get_forbidden_key():
    response = client.get(f'/manage/config/get?key={ConfigKeyEnum.TOTP_SECRET}')
    log.info(response.json())
    assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_config_set_null_deletes():
    set_response = client.post('/manage/config/set', json={'key': ConfigKeyEnum.ABOUT_CONTENT, 'value': 'to_be_deleted'})
    assert set_response.status_code == status.HTTP_200_OK
    delete_response = client.post('/manage/config/set', json={'key': ConfigKeyEnum.ABOUT_CONTENT, 'value': None})
    assert delete_response.status_code == status.HTTP_200_OK
    get_response = client.get(f'/manage/config/get?key={ConfigKeyEnum.ABOUT_CONTENT}')
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json() is None


def test_trash_list():
    response = client.get('/manage/trash/all')
    log.info(response.json())
    assert response.status_code == status.HTTP_200_OK
    trash_items = [TrashBinVO.model_validate(item) for item in response.json()]


def test_trash_recover_post():
    post_id = _create_post_and_delete()
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
    post_id = _create_post_and_delete()
    hard_delete_data = {'id': post_id, 'type': EntityTypeEnum.BLOG_POST, 'delete': True}
    edit_response = client.post('/manage/trash/edit', json=hard_delete_data)
    assert edit_response.status_code == status.HTTP_200_OK

    trash_response = client.get('/manage/trash/all')
    trash_items = [TrashBinVO.model_validate(item) for item in trash_response.json()]
    assert not any(item.id == post_id and item.type == EntityTypeEnum.BLOG_POST for item in trash_items)


def test_trash_recover_tag():
    tag_id = _create_tag_and_delete()
    recover_data = {'id': tag_id, 'type': EntityTypeEnum.POST_TAG, 'delete': False}
    edit_response = client.post('/manage/trash/edit', json=recover_data)
    assert edit_response.status_code == status.HTTP_200_OK

    all_response = client.post('/tag/all', json={'type': TagTypeEnum.POST_TAG})
    tags = [TagVO.model_validate(t) for t in all_response.json()]
    assert any(t.id == tag_id for t in tags)

    client.get(f'/tag/delete/{tag_id}')


def test_trash_unknown_entity_type():
    trash_data = {'id': 1, 'type': 'unknown_type', 'delete': False}
    response = client.post('/manage/trash/edit', json=trash_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_user_change_username():
    set_response = client.post('/manage/user', json={'username': 'test_user'})
    assert set_response.status_code == status.HTTP_200_OK
    get_response = client.get(f'/manage/config/get?key={ConfigKeyEnum.USERNAME}')
    assert get_response.status_code == status.HTTP_200_OK
    assert get_response.json() == 'test_user'

    client.post('/manage/user', json={'reset': True})


def test_user_change_password():
    set_response = client.post('/manage/user', json={'password': 'Test@1234'})
    assert set_response.status_code == status.HTTP_200_OK
    _cleanup_login_lock()
    login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234'})
    assert login_response.status_code == status.HTTP_200_OK
    _cleanup_login_lock()
    _reset_credentials()


def test_user_invalid_username():
    for invalid_name in ['abc', '1start', 'has space', 'has!char']:
        response = client.post('/manage/user', json={'username': invalid_name})
        log.info(f'{invalid_name}: {response.status_code}')
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_user_invalid_password():
    for invalid_pwd in ['short1!', 'simplepassword']:
        response = client.post('/manage/user', json={'password': invalid_pwd})
        log.info(f'{invalid_pwd}: {response.status_code}')
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_user_reset_credentials():
    client.post('/manage/user', json={'username': 'before_reset', 'password': 'BeforeReset@123'})
    reset_response = client.post('/manage/user', json={'reset': True})
    assert reset_response.status_code == status.HTTP_200_OK
    username_response = client.get(f'/manage/config/get?key={ConfigKeyEnum.USERNAME}')
    assert username_response.json() is None
    password_response = client.get(f'/manage/config/get?key={ConfigKeyEnum.PASSWORD}')
    assert password_response.json() is None


def test_totp_enforce_returns_secret():
    enforce_response = client.get('/manage/totp/enforce?enforce=True')
    assert enforce_response.status_code == status.HTTP_200_OK
    secret = enforce_response.json()
    assert secret is not None
    assert len(secret) > 0

    secret_response = client.get(f'/manage/config/get?key={ConfigKeyEnum.TOTP_SECRET}')
    assert secret_response.status_code == status.HTTP_200_OK
    assert secret_response.json() == secret

    client.get('/manage/totp/enforce?enforce=False')


def test_totp_confirm_without_secret():
    client.get('/manage/totp/enforce?enforce=False')
    confirm_response = client.get('/manage/totp/confirm?totp=000000')
    assert confirm_response.status_code == status.HTTP_406_NOT_ACCEPTABLE


def test_totp_disable():
    enforce_response = client.get('/manage/totp/enforce?enforce=True')
    secret = enforce_response.json()
    totp_client = pyotp.TOTP(secret)
    totp_code = totp_client.now()
    client.get(f'/manage/totp/confirm?totp={totp_code}')

    disable_response = client.get('/manage/totp/enforce?enforce=False')
    assert disable_response.status_code == status.HTTP_200_OK
    assert disable_response.json() is None

    enforce_config = client.get(f'/manage/config/get?key={ConfigKeyEnum.TOTP_ENFORCE}')
    assert enforce_config.json() is None
    secret_config = client.get(f'/manage/config/get?key={ConfigKeyEnum.TOTP_SECRET}')
    assert secret_config.json() is None


def test_database_download():
    response = client.get(f'/manage/database?action={DatabaseActionEnum.DOWNLOAD}')
    log.info(f'Download status: {response.status_code}, content-type: {response.headers.get("content-type")}')
    assert response.status_code == status.HTTP_200_OK


def test_database_backup():
    response = client.get(f'/manage/database?action={DatabaseActionEnum.BACKUP}')
    log.info(f'Backup status: {response.status_code}')
    assert response.status_code == status.HTTP_200_OK
