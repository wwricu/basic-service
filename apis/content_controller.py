from fastapi import APIRouter

from models import Content
from schemas import ContentInput, ContentOutput
from service import ResourceService


content_router = APIRouter(prefix="/content")


@content_router.post("", response_model=ContentOutput)
async def add_content(content: ContentInput):
    return ResourceService.add_resource(Content.init(content))


@content_router.get("",   response_model=list[ContentOutput])
async def get_content(content_id: int = None,
                      title: str = None,
                      url: str = None,
                      parent_id: int = None):
    return ResourceService.find_resources(Content(id=content_id,
                                                  title=title,
                                                  url=url,
                                                  parent_id=parent_id))


@content_router.put("", response_model=ContentOutput)
async def modify_content(content: ContentInput):
    return ResourceService.modify_resource(Content.init(content))


@content_router.delete("/{content_id}", response_model=int)
async def delete_content(content_id: int):
    return ResourceService.remove_resource(Content(id=content_id))
