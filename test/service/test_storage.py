import secrets
import uuid

import pytest

from loguru import logger as log

from wwricu.domain.third import AWSS3Object
from wwricu.component.storage import oss_private


@pytest.mark.skip
def test_oss_private_one():
    key, data = uuid.uuid4().hex, secrets.token_bytes(64)
    url = oss_private.sync_put(key, data)
    log.info(url)
    d = oss_private.sync_get(key)
    assert d == data
    oss_private.sync_delete(key)


@pytest.mark.skip
def test_oss_private_batch():
    data_len = 3
    key_list = [uuid.uuid4().hex for _ in range(data_len)]
    data_list = [secrets.token_bytes(64) for _ in range(data_len)]

    items: list[AWSS3Object] = oss_private.sync_list_all()
    origin_size = len(items)
    all_data_len = data_len + origin_size

    for i in range(data_len):
        oss_private.sync_put(key_list[i], data_list[i])

    items: list[AWSS3Object] = oss_private.sync_list_all()
    assert len(items) == all_data_len

    for _ in oss_private.sync_list_page():
        all_data_len -= 1
    assert all_data_len == 0

    oss_private.sync_batch_delete(key_list)
    items: list[AWSS3Object] = oss_private.sync_list_all()
    assert len(items) == origin_size
