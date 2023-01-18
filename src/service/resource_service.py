import os
import uuid
from datetime import datetime
from typing import Type

from models import Resource, Folder, ResourceTag, Content
from dao import BaseDao, ResourceDao
from schemas import UserOutput, ResourceQuery


class ResourceService:
    @staticmethod
    async def add_resource(resource: Resource) -> Resource:
        parent_url = ''
        if resource.parent_url is not None:
            parent = (await BaseDao.select(
                Resource(url=resource.parent_url), Resource))[0]
            parent_url = parent.url

        if isinstance(resource, Folder):
            resource.this_url = '/' + resource.title
        else:
            resource.this_url = '/' + str(uuid.uuid4())
        resource.url = parent_url + resource.this_url

        return await BaseDao.insert(resource)

    @staticmethod
    async def find_resources(resource: Resource) -> Resource:
        return await BaseDao.select(resource, resource.__class__)

    @staticmethod
    async def find_sub_resources(parent_url: str | None = None,
                                 resource_query: ResourceQuery | None = ResourceQuery(),
                                 obj_class: Type | None = Resource
                                 ) -> list[Resource]:
        return await ResourceDao.get_sub_resources(parent_url,
                                                   resource_query,
                                                   obj_class)

    @staticmethod
    async def find_sub_count(parent_url: str | None = None,
                             resource_query: ResourceQuery | None = ResourceQuery(),
                             obj_class: Type | None = Resource) -> int:
        return await ResourceDao.get_sub_resource_count(parent_url,
                                                        resource_query,
                                                        obj_class)

    @staticmethod
    async def modify_resource(resource: Resource) -> Resource:
        old_resources = await BaseDao.select(
            Resource(id=resource.id), resource.__class__)
        assert len(old_resources) == 1
        sub_resources = await ResourceService.find_sub_resources(old_resources[0].url)

        if resource.__class__ == 'Folder':
            resource.this_url = '/' + resource.title
        else:
            resource.this_url = old_resources[0].this_url

        resource.url = resource.parent_url + resource.this_url

        resource.updated_time = datetime.now()
        res = await BaseDao.update(resource, resource.__class__)
        if resource.url != old_resources[0].url:
            for re in sub_resources:
                # foreign key restraint: must update parent url to make it existing
                re.parent_url = resource.url
                await ResourceService.modify_resource(re)
        return res

    @staticmethod
    async def remove_resource(resource: Resource) -> int:
        return await BaseDao.delete(resource, Resource)

    @staticmethod
    async def reset_content_tags(content: Content):
        await BaseDao.delete_all([ResourceTag(resource_id=content.id)], ResourceTag)
        add_content_tags = [ResourceTag(resource_id=content.id,
                                        tag_id=x.id)
                            for x in content.tags]

        if len(add_content_tags) > 0:
            await BaseDao.insert_all(add_content_tags)

    @staticmethod
    async def trim_files(content_id: int, attach_files: set[str]):
        try:
            path = f'static/content/{content_id}'
            files = os.listdir(path)
            for filename in files:
                if attach_files is None or filename not in attach_files:
                    os.remove(f'{path}/{filename}')
        except Exception as e:
            print(e.__str__())

    @staticmethod
    def check_permission(
            resource: Resource,
            user: UserOutput,
            operation_mask: int) -> bool:

        permission = resource.permission % 10
        if user is not None:
            for role in user.roles:
                if role.name == 'admin':
                    return True
                if role.name == resource.group.name:
                    permission |= (resource.permission // 10) % 10
                    break
            if user.id == resource.owner_id:
                permission |= (resource.permission // 100) % 10

        if operation_mask & permission == 0:
            raise Exception('no permission')
        return True
