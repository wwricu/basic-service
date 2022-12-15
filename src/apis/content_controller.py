from fastapi import APIRouter, Response, Depends, HTTPException
from sqlalchemy.orm import Session

from models import Content, Folder
from schemas import ContentInput, ContentOutput, ContentPreview, ContentTags, UserOutput
from service import ResourceService
from core.dependency import get_db, RequiresRoles, optional_login_required


content_router = APIRouter(prefix="/content", tags=["content"])


# @content_router.post("", response_model=ContentOutput)
async def add_content(content_input: ContentInput,
                      cur_user: UserOutput = Depends(RequiresRoles('admin')),
                      db: Session = Depends(get_db)):
    content = Content.init(content_input)
    content.owner_id = cur_user.id
    content.permission = 700  # owner all, group 0, public 0
    return ContentOutput.init(ResourceService.add_resource(content, db))


# @content_router.get("", response_model=ContentOutput)
async def get_content(content_id: int,
                      cur_user: UserOutput = Depends(optional_login_required),
                      db: Session = Depends(get_db)):
    contents = ResourceService.find_resources(Content(id=content_id), db)
    if len(contents) != 1 or \
            cur_user is None and contents[0].status != 'publish':
        raise HTTPException(status_code=403, detail="need login to check draft")

    return ContentOutput.init(contents[0])


# @content_router.get("/preview/{url:path}", response_model=list[ContentPreview])
async def get_preview(url: str = None,
                      tag_id: int = 0,
                      page_idx: int = 0,
                      page_size: int = 0,
                      cur_user: UserOutput = Depends(optional_login_required),
                      db: Session = Depends(get_db)):

    folders = ResourceService.find_resources(Folder(url=url), db)
    assert len(folders) == 1
    ResourceService.check_permission(folders[0], cur_user, 1)

    contents = ResourceService.find_preview(db,
                                            folders[0].id,
                                            tag_id,
                                            page_idx,
                                            page_size)
    return [ContentPreview.init(x) for x in contents]


# @content_router.get("/count/{url:path}", response_model=int)
async def get_preview_count(url: str = None,
                            tag_id: int = 0,
                            cur_user: UserOutput = Depends(optional_login_required),
                            db: Session = Depends(get_db)):
    parent_id = 0
    if url is not None:
        folders = ResourceService.find_resources(Folder(url=url), db)
        assert len(folders) == 1
        ResourceService.check_permission(folders[0], cur_user, 1)
        parent_id = folders[0].id

    return ResourceService.find_count(db,
                                      parent_id,
                                      tag_id)


# @content_router.put("",
#                     dependencies=[Depends(RequiresRoles('admin'))],
#                     response_model=ContentOutput)
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


# @content_router.put("/tag",
#                     dependencies=[Depends(RequiresRoles('admin'))],
#                     response_model=ContentOutput)
async def modify_content_tag(content_tags: ContentTags,
                             db: Session = Depends(get_db)):
    ResourceService.modify_content_tags(content_tags.content_id,
                                        content_tags.add_tag_ids,
                                        content_tags.remove_tag_ids,
                                        db)
    return "success"
