from fastapi import APIRouter, Depends

from dao import AsyncDatabase
from schemas import TagSchema
from service import TagService
from models import Tag, PostTag
from .auth_controller import RequiresRoles


tag_router = APIRouter(prefix="/tag",
                       tags=["tag"],
                       dependencies=[Depends(AsyncDatabase.open_session)])


@tag_router.post("",
                 dependencies=[Depends(RequiresRoles('admin'))],
                 response_model=TagSchema)
async def add_tag(tag: TagSchema):
    return TagSchema.init(await TagService.add_tag(PostTag(name=tag.name)))


@tag_router.get("", response_model=list[TagSchema])
async def get_tag(tag: TagSchema = Depends()):
    tags = await TagService.find_tag(PostTag(id=tag.id, name=tag.name))
    return [TagSchema.init(x) for x in tags]


@tag_router.put("",
                dependencies=[Depends(RequiresRoles('admin'))],
                response_model=TagSchema)
async def rename_tag(tag: TagSchema):
    return TagSchema.init(
        await TagService.rename_tag(
            PostTag(id=tag.id, name=tag.name)
        )
    )


@tag_router.delete("/{tag_id}",
                   dependencies=[Depends(RequiresRoles('admin'))])
async def remove_tag(tag_id: int):
    return await TagService.remove_tag(Tag(id=tag_id))
