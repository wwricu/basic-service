import hashlib

from test_client import client, test_method


class AuthToken:
    access_token: str
    refresh_token: str
    headers: dict


def test_fake_auth():
    AuthToken.headers = {}


@test_method
def test_auth():
    password = hashlib.sha256('test_password'.encode()).hexdigest()
    payload = {
        'username': 'wwr',
        'password': password
    }
    print(
        'auth test controller',
        f'plain password: {password}'
    )
    response = client.post('/auth', data=payload)
    print(response.json())
    AuthToken.access_token = response.json()['access_token']
    AuthToken.refresh_token = response.json()['refresh_token']
    AuthToken.headers = {'Authorization': f'Bearer {AuthToken.access_token}',
                         'refresh-token': AuthToken.refresh_token}
    assert response.status_code == 200
    print(response.json())
    return response.json()


@test_method
def test_get_user():
    response = client.get('/auth', headers=AuthToken.headers)
    print(response.json())
    assert response.status_code == 200


def run_auth_all_test():
    test_auth()
    test_get_user()


if __name__ == '__main__':
    run_auth_all_test()
