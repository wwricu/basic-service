from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session

from models import Content
from schemas import ContentInput, ContentOutput
from service import ResourceService
from core.dependency import get_db


content_router = APIRouter(prefix="/content", tags=["content"])


@content_router.post("", response_model=ContentOutput)
async def add_content(content: ContentInput,
                      db: Session = Depends(get_db)):
    return ContentOutput.init(ResourceService
                              .add_resource(Content.init(content),
                                            db))


@content_router.get("",  response_model=list[ContentOutput])
async def get_content(content_id: int = None,
                      url: str = None,
                      parent_id: int = None,
                      author_id: int = None,
                      db: Session = Depends(get_db)):

    contents = ResourceService.find_resources(Content(id=content_id,
                                                      url=url,
                                                      parent_id=parent_id,
                                                      author_id=author_id),
                                              db)
    return [ContentOutput.init(x) for x in contents]


@content_router.put("", response_model=ContentOutput)
async def modify_content(content: ContentInput,
                         db: Session = Depends(get_db)):
    return ContentOutput.init(ResourceService
                              .modify_resource(Content.init(content), db))


@content_router.delete("/{content_id}")
async def delete_content(content_id: int,
                         db: Session = Depends(get_db)):
    ResourceService.remove_resource(Content(id=content_id), db)
    return Response(status_code=200)
