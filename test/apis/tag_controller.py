from test import client
from test.apis import AuthToken
from test.apis.auth_controller import test_auth
from test.apis.content_controller import test_add_content

from src.schemas import ContentInput, TagSchema


def test_add_tag(tag_name: str):
    tag = TagSchema(name=tag_name)
    response = client.post('/tag',
                           json=tag.dict(),
                           headers=AuthToken.headers)
    assert response.status_code == 200
    return response

def test_add_category(cat_name: str):
    tag = TagSchema(name=cat_name)
    response = client.post('/category',
                           json=tag.dict(),
                           headers=AuthToken.headers)
    assert response.status_code == 200
    return response
    pass

def test_modify_content(cat_name: str, tag_name: str):
    response = test_add_content()
    response = client.get(f'/content/{response.json()}',
                          headers=AuthToken.headers)
    new_content = response.json()
    new_content['category_name'] = cat_name
    new_content['tags'] = [{'name': tag_name}]
    client.put('/content',
               json=new_content,
               headers=AuthToken.headers)

def run_tag_all_test():
    test_auth()
    tag_name = 'test tag name'
    test_add_tag(tag_name)
    cat_name = 'test cat name'
    test_add_category(cat_name)
    test_modify_content(cat_name, tag_name)

if __name__ == '__main__':
    run_tag_all_test()