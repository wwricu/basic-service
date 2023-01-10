from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas import TagSchema
from service import TagService, DatabaseService
from models import Tag, PostTag
from .auth_controller import RequiresRoles


tag_router = APIRouter(prefix="/tag", tags=["tag"])


@tag_router.post("",
                 dependencies=[Depends(RequiresRoles('admin'))],
                 response_model=TagSchema)
async def add_tag(tag: TagSchema,
                  db: Session = Depends(DatabaseService.get_db)):
    return TagSchema.init(TagService.add_tag(PostTag(name=tag.name), db))


@tag_router.get("", response_model=list[TagSchema])
async def get_tag(tag_id: int = None,
                  name: str = None,
                  db: Session = Depends(DatabaseService.get_db)):
    tags = TagService.find_tag(PostTag(id=tag_id, name=name), db)
    return [TagSchema.init(x) for x in tags]


@tag_router.put("",
                dependencies=[Depends(RequiresRoles('admin'))],
                response_model=TagSchema)
async def rename_tag(tag: TagSchema,
                     db: Session = Depends(DatabaseService.get_db)):
    return TagSchema.init(TagService
                          .rename_tag(PostTag(id=tag.id, name=tag.name), db))


@tag_router.delete("/{tag_id}",
                   dependencies=[Depends(RequiresRoles('admin'))],
                   response_model=int)
async def remove_tag(tag_id: int,
                     db: Session = Depends(DatabaseService.get_db)):
    return TagService.remove_tag(Tag(id=tag_id), db)
