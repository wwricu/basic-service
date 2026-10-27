import uuid

from fastapi import status

from test.api.utils import create_tag, delete_tag
from test.test_utils import client
from wwricu.domain.enum import TagTypeEnum
from wwricu.domain.tag import TagVO


def test_tag_lifecycle():
    for tag_type in TagTypeEnum:
        tag = create_tag(tag_type=tag_type)
        try:
            assert tag.id in _tag_ids(tag_type)
            duplicate = client.post('/admin/tag/create', json={'name': tag.name, 'type': tag.type})
            assert duplicate.status_code == status.HTTP_409_CONFLICT

            new_name = f'updated_{uuid.uuid4().hex[:8]}'
            response = client.post('/admin/tag/update', json={'id': tag.id, 'name': new_name, 'type': tag_type})
            assert response.status_code == status.HTTP_200_OK
            assert TagVO.model_validate(response.json()).name == new_name
        finally:
            delete_tag(tag.id)
        assert tag.id not in _tag_ids(tag_type)


def _tag_ids(tag_type: TagTypeEnum) -> list[int]:
    response = client.post('/admin/tag/all', json={'type': tag_type})
    assert response.status_code == status.HTTP_200_OK
    return [TagVO.model_validate(tag).id for tag in response.json()]
