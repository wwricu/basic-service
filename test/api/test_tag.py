import uuid

from fastapi import status
from loguru import logger as log

from test.api.utils import create_tag, delete_tag
from test.test_utils import client
from wwricu.domain.enum import TagTypeEnum
from wwricu.domain.tag import TagVO


def test_create_tag():
    for tag_type in [TagTypeEnum.POST_TAG, TagTypeEnum.POST_CAT]:
        tag = create_tag(tag_type=tag_type)
        try:
            assert tag.id is not None
            assert tag.name is not None
            assert tag.type == tag_type
        finally:
            delete_tag(tag.id)


def test_create_duplicate_tag():
    tag_name = f'dup_test_{uuid.uuid4().hex[:8]}'
    tag = create_tag(name=tag_name, tag_type=TagTypeEnum.POST_TAG)
    try:
        dup_response = client.post('/tag/create', json={'name': tag_name, 'type': TagTypeEnum.POST_TAG})
        log.info(dup_response.json())
        assert dup_response.status_code == status.HTTP_409_CONFLICT
    finally:
        delete_tag(tag.id)


def test_create_tag_after_delete():
    tag_name = f'recreate_test_{uuid.uuid4().hex[:8]}'
    tag = create_tag(name=tag_name, tag_type=TagTypeEnum.POST_TAG)
    delete_tag(tag.id)
    recreate_response = client.post('/tag/create', json={'name': tag_name, 'type': TagTypeEnum.POST_TAG})
    assert recreate_response.status_code == status.HTTP_200_OK
    new_tag = TagVO.model_validate(recreate_response.json())
    assert new_tag.name == tag_name
    delete_tag(new_tag.id)


def test_get_all_tags():
    for tag_type in [TagTypeEnum.POST_TAG, TagTypeEnum.POST_CAT]:
        response = client.post('/tag/all', json={'type': tag_type})
        log.info(response.json())
        assert response.status_code == status.HTTP_200_OK
        tags = [TagVO.model_validate(t) for t in response.json()]
        for tag in tags:
            assert tag.type == tag_type


def test_update_tag():
    tag = create_tag(tag_type=TagTypeEnum.POST_TAG)
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
        delete_tag(tag.id)


def test_update_tag_duplicate_name():
    tag1 = create_tag(tag_type=TagTypeEnum.POST_TAG)
    tag2 = create_tag(tag_type=TagTypeEnum.POST_TAG)
    try:
        update_data = {'id': tag2.id, 'name': tag1.name, 'type': tag1.type}
        response = client.post('/tag/update', json=update_data)
        log.info(response.json())
        assert response.status_code == status.HTTP_409_CONFLICT
    finally:
        delete_tag(tag1.id)
        delete_tag(tag2.id)


def test_update_tag_not_found():
    update_data = {'id': 99999, 'name': 'not_found', 'type': TagTypeEnum.POST_TAG}
    response = client.post('/tag/update', json=update_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_tag_same_name():
    tag = create_tag(tag_type=TagTypeEnum.POST_TAG)
    try:
        update_data = {'id': tag.id, 'name': tag.name, 'type': tag.type}
        response = client.post('/tag/update', json=update_data)
        assert response.status_code == status.HTTP_200_OK
        updated = TagVO.model_validate(response.json())
        assert updated.name == tag.name
    finally:
        delete_tag(tag.id)


def test_delete_tag():
    tag = create_tag(tag_type=TagTypeEnum.POST_TAG)
    delete_response = client.get(f'/tag/delete/{tag.id}')
    assert delete_response.status_code == status.HTTP_200_OK
    all_response = client.post('/tag/all', json={'type': TagTypeEnum.POST_TAG})
    tags = [TagVO.model_validate(t) for t in all_response.json()]
    tag_ids = [t.id for t in tags]
    assert tag.id not in tag_ids
