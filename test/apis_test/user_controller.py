from test_client import client, test_method
from apis_test import AuthToken
from apis_test.auth_controller import test_auth

from schemas import UserInput


@test_method
def test_add_user() -> int:
    user_input = UserInput(
        username='test user',
        password='test password',
        email='test@email.test',
    )
    response = client.post('user',
                           json=user_input.dict(),
                           headers=AuthToken.headers)
    print(response.json())
    assert response.status_code == 200
    return response.json()['id']


@test_method
def test_remove_user(user_id: int):
    response = client.delete(f'/user/{user_id}',
                             headers=AuthToken.headers)
    assert response.status_code == 200


@test_method
def test_get_user(user_id: int):
    response = client.get(f'/user/{user_id}',
                          headers=AuthToken.headers)
    print(response.json())
    assert response.status_code == 200
    assert response.json()[1]['username'] == 'after change'
    return response.json()[1]['id']


@test_method
def test_modify_user(user_id: int):
    user_input = UserInput(id=user_id,
                           username='after change')
    response = client.put('/user',
                          json=user_input.dict(),
                          headers=AuthToken.headers)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['username'] == 'after change'
    assert response.json()['email'] == 'test@email.test'


def run_user_all_test():
    test_auth()
    new_id = test_add_user()
    test_modify_user(new_id)
    test_get_user(new_id)
    test_remove_user(new_id)


if __name__ == '__main__':
    run_user_all_test()
