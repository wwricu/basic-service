from test import client
from test.apis import AuthToken
from test.apis.auth_controller import test_auth

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

def test_delete_category(folder_id: int):
    return client.delete(f'/folder/{folder_id}',
                         headers=AuthToken.headers)

def test_get_count():
    return client.get('/folder/count//post')

def run_folder_all_test():
    test_auth()
    r = test_add_category('/post', 'test category')
    assert r.status_code == 200
    test_auth()
    print(r.json())
    r = test_delete_category(r.json()['id'])
    assert r.status_code == 200
    r = test_get_count()
    print(r.json())
    assert r.status_code == 200

if __name__ == '__main__':
    run_folder_all_test()
