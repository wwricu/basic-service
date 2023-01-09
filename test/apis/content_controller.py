from test import client
from test.apis import AuthToken
from test.apis.auth_controller import test_auth

from src.schemas import ContentInput


def test_add_content():
    content_input = {
        'title': 'test title',
        'parent_url': '/draft',
        'permission': 700,
        'content': 'test content',
    }
    response = client.post('/content',
                           json=content_input,
                           headers=AuthToken.headers)
    print(response.json())
    assert response.status_code == 200
    return response


def test_modify_content(content_id: int):
    content_input = ContentInput(id=content_id,
                                 title='after change title',
                                 parent_url='/post',
                                 permission=711)
    print(content_input.dict())
    response = client.put('/content',
                          json=content_input.dict(),
                          headers=AuthToken.headers)
    print(response.json())
    assert response.status_code == 200
    return response


def test_delete_content(content_id: int):
    response = client.delete(f'content/{content_id}',
                             headers=AuthToken.headers)
    assert response.status_code == 200
    return response


def run_content_all_test():
    test_auth()
    r = test_add_content()
    test_modify_content(r.json())
    test_delete_content(r.json())


if __name__ == '__main__':
    run_content_all_test()
