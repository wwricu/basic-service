import uuid

from loguru import logger as log
from fastapi import status

from wwricu.domain.enum import TagTypeEnum

from test.test_utils import client
from wwricu.domain.tag import TagVO, TagRO


def test_create_tag():
    for tag_type in TagTypeEnum.POST_TAG, TagTypeEnum.POST_CAT:
        tag_name, tag_id = uuid.uuid4().hex, None
        tag_ro = TagRO(name=tag_name, type=tag_type)

        try:
            # create tag
            response = client.post('/tag/create', json=tag_ro.model_dump())
            log.info(response.json())
            assert response.status_code == status.HTTP_200_OK
            tag = TagVO.model_validate(response.json())
            tag_id = tag.id

            # create tag with same name and type
            response = client.post('/tag/create', json=tag_ro.model_dump())
            assert response.status_code != status.HTTP_200_OK  # shall fail

            response = client.get(f'/tag/delete/{tag.id}')
            assert response.status_code == status.HTTP_200_OK

            # create tag with same name and type
            response = client.post('/tag/create', json=tag_ro.model_dump())
            assert response.status_code == status.HTTP_200_OK  # shall succeed

        finally:
            if tag_id is not None:
                client.get(f'/tag/delete/{tag_id}')
