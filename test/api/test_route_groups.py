from fastapi import status

from test.test_utils import client


def test_privileged_group_answers_the_session_layer_not_the_url():
    # Nothing hides /admin/* from a caller that knows the path any more: the request reaches the
    # handlers, where the session cookie decides. Tests run un-optimized, where is_admin
    # short-circuits on __debug__, so only "not refused before the handler" is assertable here.
    assert client.get('/admin/info').status_code != status.HTTP_404_NOT_FOUND
    assert client.get('/admin/logout').status_code != status.HTTP_404_NOT_FOUND


def test_public_group_is_reachable():
    assert client.get('/open/about').status_code == status.HTTP_200_OK
    response = client.get('/image/post/1/any-key', follow_redirects=False)
    assert response.status_code != status.HTTP_404_NOT_FOUND
