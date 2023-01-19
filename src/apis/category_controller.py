from fastapi import APIRouter, Depends

from dao import AsyncDatabase
from schemas import TagSchema
from service import TagService, RequiresRoles
from models import PostCategory, Tag


category_router = APIRouter(prefix="/category",
                            tags=["category"],
                            dependencies=[Depends(AsyncDatabase.open_session)])


@category_router.post("",
                      dependencies=[Depends(RequiresRoles('admin'))],
                      response_model=TagSchema)
async def add_category(category: TagSchema):
    return TagSchema.init(
        await TagService.add_tag(PostCategory(name=category.name))
    )


@category_router.get("", response_model=list[TagSchema])
async def get_category(category: TagSchema = Depends()):
    tags = await TagService.find_tag(
        PostCategory(id=category.id, name=category.name)
    )
    return [TagSchema.init(x) for x in tags]


@category_router.put("",
                     dependencies=[Depends(RequiresRoles('admin'))],
                     response_model=TagSchema)
async def rename_category(category: TagSchema):
    return TagSchema.init(await TagService.rename_tag(
        PostCategory(id=category.id, name=category.name)
    ))


@category_router.delete("/{category_id}",
                        dependencies=[Depends(RequiresRoles('admin'))])
async def remove_tag(category_id: int):
    return await TagService.remove_tag(Tag(id=category_id))
