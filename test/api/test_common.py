import pyotp
from fastapi import status
from loguru import logger as log

from test.api.utils import reset_credentials, set_password
from test.test_utils import client
from wwricu.domain.constant import CommonConstant


def test_login_wrong_password():
    set_password('Test@1234')
    try:
        response = client.post('/login', json={'username': 'wwr', 'password': 'wrong_password'})
        log.info(response.json())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        reset_credentials()


def test_login_and_logout():
    set_password('Test@1234')
    try:
        login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234'})
        assert login_response.status_code == status.HTTP_200_OK
        assert CommonConstant.SESSION_ID in login_response.cookies
        logout_response = client.get('/logout')
        log.info(f'Logout status: {logout_response.status_code}')
        assert logout_response.status_code == status.HTTP_200_OK
    finally:
        reset_credentials()


def test_change_password_and_login():
    first_password = 'First@1234'
    second_password = 'Second@5678'
    set_password(first_password)
    try:
        response = client.post('/login', json={'username': 'wwr', 'password': first_password})
        assert response.status_code == status.HTTP_200_OK

        set_password(second_password)

        response = client.post('/login', json={'username': 'wwr', 'password': first_password})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = client.post('/login', json={'username': 'wwr', 'password': second_password})
        assert response.status_code == status.HTTP_200_OK
    finally:
        reset_credentials()


def test_totp_enforce_confirm_login_disable():
    set_password('Test@1234')
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

        totp_code = totp_client.now()
        login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234', 'totp': totp_code})
        assert login_response.status_code == status.HTTP_200_OK

        login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234', 'totp': '000000'})
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED

        disable_response = client.get('/manage/totp/enforce?enforce=False')
        assert disable_response.status_code == status.HTTP_200_OK

        login_response = client.post('/login', json={'username': 'wwr', 'password': 'Test@1234'})
        assert login_response.status_code == status.HTTP_200_OK
    finally:
        client.get('/manage/totp/enforce?enforce=False')
        reset_credentials()


def test_info():
    response = client.get('/info')
    log.info(response.status_code)
    assert response.status_code == status.HTTP_200_OK
