import uuid

from fastapi import status
from loguru import logger as log

from test.test_utils import client
from wwricu.domain.enum import TagTypeEnum
from wwricu.domain.tag import TagVO


def _create_tag(name: str | None = None, tag_type: TagTypeEnum = TagTypeEnum.POST_TAG) -> TagVO:
    tag_name = name or f'test_{tag_type}_{uuid.uuid4().hex[:8]}'
    response = client.post('/tag/create', json={'name': tag_name, 'type': tag_type})
    assert response.status_code == status.HTTP_200_OK
    return TagVO.model_validate(response.json())


def _delete_tag(tag_id: int):
    client.get(f'/tag/delete/{tag_id}')


def test_create_tag():
    for tag_type in [TagTypeEnum.POST_TAG, TagTypeEnum.POST_CAT]:
        tag = _create_tag(tag_type=tag_type)
        try:
            assert tag.id is not None
            assert tag.name is not None
            assert tag.type == tag_type
        finally:
            _delete_tag(tag.id)


def test_create_duplicate_tag():
    tag_name = f'dup_test_{uuid.uuid4().hex[:8]}'
    tag = _create_tag(name=tag_name, tag_type=TagTypeEnum.POST_TAG)
    try:
        dup_response = client.post('/tag/create', json={'name': tag_name, 'type': TagTypeEnum.POST_TAG})
        log.info(dup_response.json())
        assert dup_response.status_code == status.HTTP_409_CONFLICT
    finally:
        _delete_tag(tag.id)


def test_create_tag_after_delete():
    tag_name = f'recreate_test_{uuid.uuid4().hex[:8]}'
    tag = _create_tag(name=tag_name, tag_type=TagTypeEnum.POST_TAG)
    _delete_tag(tag.id)
    recreate_response = client.post('/tag/create', json={'name': tag_name, 'type': TagTypeEnum.POST_TAG})
    assert recreate_response.status_code == status.HTTP_200_OK
    new_tag = TagVO.model_validate(recreate_response.json())
    assert new_tag.name == tag_name
    _delete_tag(new_tag.id)


def test_get_all_tags():
    for tag_type in [TagTypeEnum.POST_TAG, TagTypeEnum.POST_CAT]:
        response = client.post('/tag/all', json={'type': tag_type})
        log.info(response.json())
        assert response.status_code == status.HTTP_200_OK
        tags = [TagVO.model_validate(t) for t in response.json()]
        for tag in tags:
            assert tag.type == tag_type


def test_update_tag():
    tag = _create_tag(tag_type=TagTypeEnum.POST_TAG)
    try:
        new_name = f'updated_{uuid.uuid4().hex[:8]}'
        update_data = {'id': tag.id, 'name': new_name, 'type': tag.type}
        response = client.post('/tag/update', json=update_data)
        log.info(response.json())
        assert response.status_code == status.HTTP_200_OK
        updated = TagVO.model_validate(response.json())
        assert updated.id == tag.id
        assert updated.name == new_name
    finally:
        _delete_tag(tag.id)


def test_update_tag_duplicate_name():
    tag1 = _create_tag(tag_type=TagTypeEnum.POST_TAG)
    tag2 = _create_tag(tag_type=TagTypeEnum.POST_TAG)
    try:
        update_data = {'id': tag2.id, 'name': tag1.name, 'type': tag1.type}
        response = client.post('/tag/update', json=update_data)
        log.info(response.json())
        assert response.status_code == status.HTTP_409_CONFLICT
    finally:
        _delete_tag(tag1.id)
        _delete_tag(tag2.id)


def test_update_tag_not_found():
    update_data = {'id': 99999, 'name': 'not_found', 'type': TagTypeEnum.POST_TAG}
    response = client.post('/tag/update', json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_tag_same_name():
    tag = _create_tag(tag_type=TagTypeEnum.POST_TAG)
    try:
        update_data = {'id': tag.id, 'name': tag.name, 'type': tag.type}
        response = client.post('/tag/update', json=update_data)
        assert response.status_code == status.HTTP_200_OK
        updated = TagVO.model_validate(response.json())
        assert updated.name == tag.name
    finally:
        _delete_tag(tag.id)


def test_delete_tag():
    tag = _create_tag(tag_type=TagTypeEnum.POST_TAG)
    delete_response = client.get(f'/tag/delete/{tag.id}')
    assert delete_response.status_code == status.HTTP_200_OK
    all_response = client.post('/tag/all', json={'type': TagTypeEnum.POST_TAG})
    tags = [TagVO.model_validate(t) for t in all_response.json()]
    tag_ids = [t.id for t in tags]
    assert tag.id not in tag_ids


def test_tag_lifecycle():
    tag_name = f'lifecycle_{uuid.uuid4().hex[:8]}'
    create_response = client.post('/tag/create', json={'name': tag_name, 'type': TagTypeEnum.POST_TAG})
    assert create_response.status_code == status.HTTP_200_OK
    tag = TagVO.model_validate(create_response.json())

    all_response = client.post('/tag/all', json={'type': TagTypeEnum.POST_TAG})
    tags = [TagVO.model_validate(t) for t in all_response.json()]
    assert any(t.id == tag.id for t in tags)

    new_name = f'lifecycle_updated_{uuid.uuid4().hex[:8]}'
    update_response = client.post('/tag/update', json={'id': tag.id, 'name': new_name, 'type': tag.type})
    assert update_response.status_code == status.HTTP_200_OK
    updated = TagVO.model_validate(update_response.json())
    assert updated.name == new_name

    client.get(f'/tag/delete/{tag.id}')
    all_response = client.post('/tag/all', json={'type': TagTypeEnum.POST_TAG})
    tags = [TagVO.model_validate(t) for t in all_response.json()]
    assert not any(t.id == tag.id for t in tags)

    recreate_response = client.post('/tag/create', json={'name': tag_name, 'type': TagTypeEnum.POST_TAG})
    assert recreate_response.status_code == status.HTTP_200_OK
    new_tag = TagVO.model_validate(recreate_response.json())
    _delete_tag(new_tag.id)
