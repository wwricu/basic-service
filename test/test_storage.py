import secrets
import uuid

from wwricu.service.storage import put_object, get_object


def test_storage():
    file = secrets.token_bytes(64)
    key = f'posts/{0}/{uuid.uuid4().hex}'
    put_object(key, file)
    f = get_object(key)
    assert f == file
