from fastapi import status

from test.test_utils import client
from wwricu.config import env
from wwricu.domain.constant import CommonConst

EDGE_TOKEN = 'test-edge-token'


def test_privileged_group_is_invisible_without_the_edge_token(monkeypatch):
    monkeypatch.setattr(env, 'ADMIN_API_TOKEN', EDGE_TOKEN)
    assert client.get('/admin/info').status_code == status.HTTP_404_NOT_FOUND
    assert client.get('/admin/logout').status_code == status.HTTP_404_NOT_FOUND
    assert client.post('/admin/manage/user', json={'reset': True}).status_code == status.HTTP_404_NOT_FOUND


def test_a_wrong_edge_token_is_the_same_404(monkeypatch):
    monkeypatch.setattr(env, 'ADMIN_API_TOKEN', EDGE_TOKEN)
    response = client.get('/admin/info', headers={CommonConst.ADMIN_TOKEN_HEADER: 'guess'})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_the_edge_token_opens_the_gate(monkeypatch):
    monkeypatch.setattr(env, 'ADMIN_API_TOKEN', EDGE_TOKEN)
    response = client.get('/admin/info', headers={CommonConst.ADMIN_TOKEN_HEADER: EDGE_TOKEN})
    # not the guard's 404 any more; the session check behind it answers. Tests run un-optimized,
    # where is_admin short-circuits on __debug__, so 401 is not assertable here.
    assert response.status_code != status.HTTP_404_NOT_FOUND


def test_public_group_is_reachable_without_the_edge_token(monkeypatch):
    monkeypatch.setattr(env, 'ADMIN_API_TOKEN', EDGE_TOKEN)
    assert client.get('/open/about').status_code == status.HTTP_200_OK
    response = client.get('/image/post/1/any-key', follow_redirects=False)
    assert response.status_code != status.HTTP_404_NOT_FOUND
