from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas import TagSchema
from service import TagService
from models import PostCategory
from core.dependency import get_db, RequiresRoles


category_router = APIRouter(prefix="/category", tags=["category"])


@category_router.post("",
                      dependencies=[Depends(RequiresRoles('admin'))],
                      response_model=TagSchema)
async def add_category(category: TagSchema,
                       db: Session = Depends(get_db)):
    return TagSchema.init(TagService.add_tag(PostCategory(name=category.name), db))


@category_router.get("", response_model=list[TagSchema])
async def get_category(tag_id: int = None,
                       name: str = None,
                       db: Session = Depends(get_db)):
    tags = TagService.find_tag(PostCategory(id=tag_id, name=name), db)
    return [TagSchema.init(x) for x in tags]


@category_router.put("",
                     dependencies=[Depends(RequiresRoles('admin'))],
                     response_model=TagSchema)
async def rename_category(category: TagSchema,
                          db: Session = Depends(get_db)):
    return TagSchema.init(TagService
                          .rename_tag(PostCategory(id=category.id,
                                                   name=category.name), db))
