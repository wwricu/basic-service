from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from schemas import TagSchema, TagContents
from service import TagService
from models import Tag
from core.dependency import get_db


tag_router = APIRouter(prefix="/tag", tags=["tag"])


@tag_router.post("", response_model=TagSchema)
async def add_tag(tag: TagSchema,
                  db: Session = Depends(get_db)):
    return TagSchema.init(TagService.add_tag(Tag.init(tag), db))


@tag_router.get("", response_model=list[TagSchema])
async def get_tag(tag_id: int = None,
                  name: str = None,
                  db: Session = Depends(get_db)):
    tags = TagService.find_tag(Tag(id=tag_id, name=name), db)
    return [TagSchema.init(x) for x in tags]


@tag_router.put("/content", response_model=TagSchema)
async def rename_tag(tag: TagSchema,
                     db: Session = Depends(get_db)):
    return TagSchema.init(TagService
                          .rename_tag(Tag(id=tag.id, name=tag.name), db))


@tag_router.put("/content")
async def modify_tag(tag_content: TagContents,
                     db: Session = Depends(get_db)):
    TagService.modify_tag_content(tag_content.tag_id,
                                  tag_content.add_content_ids,
                                  tag_content.remove_content_ids,
                                  db)
    return "success"


@tag_router.delete("/{tag_id}", response_model=int)
async def remove_tag(tag_id: int,
                     db: Session = Depends(get_db)):
    return TagService.remove_tag(Tag(id=tag_id), db)
