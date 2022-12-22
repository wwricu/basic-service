from test import client
from test.apis import AuthToken
from test.apis.auth_controller import test_auth, test_fake_auth

from src.schemas import FolderInput

def test_get_folder(url: str):
    response = client.get(f'/folder/sub_resources/{url}',
                          headers=AuthToken.headers)
    print(response.json())
    return response

def test_add_category(parent_url: str, title: str):
    folder_input = FolderInput(title=title,
                               parent_url=parent_url)
    response = client.post('/folder',
                           json=folder_input.dict(),
                           headers=AuthToken.headers)
    print(response.json())
    return response

def test_delete_category(url: str):
    return client.delete(f'/folder/{url}',
                         headers=AuthToken.headers)

def run_all_test():
    test_auth()
    r = test_add_category('/post', 'test%20category')
    assert r.status_code == 200
    r = test_get_folder('/post')
    assert r.status_code == 200
    r = test_delete_category('/post/test%20category')
    assert r.status_code == 200

if __name__ == '__main__':
    run_all_test()
