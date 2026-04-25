import asyncio

import pyotp
from fastapi import status
from loguru import logger as log

from test.test_utils import client
from wwricu.component.cache import sys_cache
from wwricu.domain.constant import CommonConstant
from wwricu.domain.enum import CacheKeyEnum


def _cleanup_login_lock():
    for key in list(sys_cache.cache_data.keys()):
        if key.startswith('login_retries:'):
            asyncio.run(sys_cache.delete(key))


def _set_password(password: str):
    response = client.post('/manage/user', json={'password': password})
    assert response.status_code == status.HTTP_200_OK


def _reset_credentials():
    response = client.post('/manage/user', json={'reset': True})
    assert response.status_code == status.HTTP_200_OK


def test_login_wrong_password():
    _cleanup_login_lock()
    _set_password('Test@1234')
    try:
        response = client.post('/login', json={'username': 'wwr', 'password': 'wrong_password'})
        log.info(response.json())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        _cleanup_login_lock()
        _reset_credentials()


def test_login_wrong_username():
    _cleanup_login_lock()
    _set_password('Test@1234')
    try:
        response = client.post('/login', json={'username': 'wrong_user', 'password': 'Test@1234'})
        log.info(response.json())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        _cleanup_login_lock()
        _reset_credentials()


def test_login_success():
    _cleanup_login_lock()
    _set_password('Test@1234')
    try:
        response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234'})
        log.info(response.json())
        assert response.status_code == status.HTTP_200_OK
        assert CommonConstant.SESSION_ID in response.cookies
        assert CommonConstant.COOKIE_SIGN in response.cookies
    finally:
        _cleanup_login_lock()
        _reset_credentials()


def test_login_and_logout():
    _cleanup_login_lock()
    _set_password('Test@1234')
    try:
        login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234'})
        assert login_response.status_code == status.HTTP_200_OK
        assert CommonConstant.SESSION_ID in login_response.cookies
        logout_response = client.get('/logout')
        log.info(f'Logout status: {logout_response.status_code}')
        assert logout_response.status_code == status.HTTP_200_OK
    finally:
        _cleanup_login_lock()
        _reset_credentials()


def test_change_password_and_login():
    _cleanup_login_lock()
    first_password = 'First@1234'
    second_password = 'Second@5678'
    _set_password(first_password)
    try:
        response = client.post('/login', json={'username': 'wwr', 'password': first_password})
        assert response.status_code == status.HTTP_200_OK

        _cleanup_login_lock()
        _set_password(second_password)

        response = client.post('/login', json={'username': 'wwr', 'password': first_password})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        _cleanup_login_lock()
        response = client.post('/login', json={'username': 'wwr', 'password': second_password})
        assert response.status_code == status.HTTP_200_OK
    finally:
        _cleanup_login_lock()
        _reset_credentials()


def test_reset_password_and_login():
    _cleanup_login_lock()
    _set_password('Test@1234')
    try:
        response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234'})
        assert response.status_code == status.HTTP_200_OK
        _reset_credentials()
        _cleanup_login_lock()
        response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        _cleanup_login_lock()
        _reset_credentials()


def test_totp_enforce_confirm_login_disable():
    _cleanup_login_lock()
    _set_password('Test@1234')
    try:
        enforce_response = client.get('/manage/totp/enforce?enforce=True')
        assert enforce_response.status_code == status.HTTP_200_OK
        secret = enforce_response.json()
        log.info(f'TOTP secret: {secret}')

        totp_client = pyotp.TOTP(secret)
        totp_code = totp_client.now()
        confirm_response = client.get(f'/manage/totp/confirm?totp={totp_code}')
        assert confirm_response.status_code == status.HTTP_200_OK

        login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234'})
        assert login_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        _cleanup_login_lock()
        totp_code = totp_client.now()
        login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234', 'totp': totp_code})
        assert login_response.status_code == status.HTTP_200_OK

        _cleanup_login_lock()
        login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234', 'totp': '000000'})
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED

        _cleanup_login_lock()
        disable_response = client.get('/manage/totp/enforce?enforce=False')
        assert disable_response.status_code == status.HTTP_200_OK

        login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234'})
        assert login_response.status_code == status.HTTP_200_OK
    finally:
        _cleanup_login_lock()
        client.get('/manage/totp/enforce?enforce=False')
        _reset_credentials()


def test_info():
    response = client.get('/info')
    log.info(response.status_code)
    assert response.status_code == status.HTTP_200_OK
