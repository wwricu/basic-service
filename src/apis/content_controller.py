from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session

from models import Content
from schemas import ContentInput, ContentOutput, ContentPreview, ContentTags
from service import ResourceService
from core.dependency import get_db, RequiresRoles


content_router = APIRouter(prefix="/content", tags=["content"])


@content_router.post("",
                     dependencies=[Depends(RequiresRoles('admin'))],
                     response_model=ContentOutput)
async def add_content(content: ContentInput,
                      db: Session = Depends(get_db)):
    return ContentOutput.init(ResourceService
                              .add_resource(Content.init(content),
                                            db))


@content_router.get("", response_model=ContentOutput)
async def get_content(content_id: int, db: Session = Depends(get_db)):
    contents = ResourceService.find_resources(Content(id=content_id), db)
    return ContentOutput.init(contents[0]) if len(contents) == 1 else {}


@content_router.get("/preview", response_model=list[ContentPreview])
async def get_preview(parent_id: int = 0,
                      status: str = 'publish',
                      tag_id: int = 0,
                      page_idx: int = 0,
                      page_size: int = 0,
                      db: Session = Depends(get_db)):

    contents = ResourceService.find_preview(db,
                                            parent_id,
                                            status,
                                            tag_id,
                                            page_idx,
                                            page_size)
    return [ContentPreview.init(x) for x in contents]


@content_router.get("/count", response_model=int)
async def get_preview_count(parent_id: int = 0,
                            status: str = 'publish',
                            tag_id: int = 0,
                            db: Session = Depends(get_db)):

    return ResourceService.find_count(db,
                                      parent_id,
                                      status,
                                      tag_id)


@content_router.put("",
                    dependencies=[Depends(RequiresRoles('admin'))],
                    response_model=ContentOutput)
async def modify_content(content: ContentInput,
                         db: Session = Depends(get_db)):
    ResourceService.reset_content_tags(Content.init(content), db)
    return ContentOutput.init(ResourceService
                              .modify_resource(Content.init(content), db))


@content_router.delete("/{content_id}",
                       dependencies=[Depends(RequiresRoles('admin'))])
async def delete_content(content_id: int,
                         db: Session = Depends(get_db)):
    ResourceService.remove_resource(Content(id=content_id), db)
    return Response(status_code=200)


@content_router.put("/tag",
                    dependencies=[Depends(RequiresRoles('admin'))],
                    response_model=ContentOutput)
async def modify_content_tag(content_tags: ContentTags,
                             db: Session = Depends(get_db)):
    ResourceService.modify_content_tags(content_tags.content_id,
                                        content_tags.add_tag_ids,
                                        content_tags.remove_tag_ids,
                                        db)
    return "success"
