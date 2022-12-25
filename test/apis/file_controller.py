from test import client
from test.apis import AuthToken
from test.apis.auth_controller import test_auth


def test_upload_static_file() -> int:
    response = client.post('/file/static',
                           data={'filename': 'test_file',
                                 "msg": "hello",
                                 "type": "multipart/form-data"
                           },
                           files={
                               "files": 'test file'.encode()
                           },
                           headers=AuthToken.headers)
    print(response.json())
    assert response.status_code == 200
    return response

def run_user_all_test():
    test_auth()
    test_upload_static_file()

if __name__ == '__main__':
    run_user_all_test()
