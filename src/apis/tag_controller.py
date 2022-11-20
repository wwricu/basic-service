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


@tag_router.delete("/{tag_id}", response_model=int)
async def remove_tag(tag_id: int,
                     db: Session = Depends(get_db)):
    return TagService.remove_tag(Tag(id=tag_id), db)


@tag_router.put("")
async def modify_tag(tag_content: TagContents,
                     db: Session = Depends(get_db)):
    TagService.modify_tag_content(tag_content.tag_id,
                                  tag_content.add_content_ids,
                                  tag_content.remove_content_ids,
                                  db)
    return "success"
