from fastapi import APIRouter, Depends
from sqlalchemy import update, select

from domain.entity import BlogPost
from wwricu.domain.entity import PostCategory
from wwricu.domain.input import CategoryRO
from wwricu.domain.output import CategoryVO
from wwricu.service.common import admin_only
from wwricu.service.database import session


tag_api = APIRouter(prefix='/category', tags=['Tag Management'], dependencies=[Depends(admin_only)])


@tag_api.post('/create', response_model=CategoryVO)
async def create_tag(category_create: CategoryRO) -> CategoryVO:
    category = PostCategory(name=category_create.name, parent=category_create.parent)
    session.add(category)
    await session.flush()
    return CategoryVO.model_validate(category)


@tag_api.post('/update', response_model=CategoryVO)
async def update_tag(category_update: CategoryRO) -> CategoryVO:
    stmt = update(PostCategory).where(
        PostCategory.id == category_update.id).values(
        name=category_update.name,
        parent=category_update.parent,
        description=category_update.description
    )
    await session.execute(stmt)
    stmt = select(PostCategory).where(PostCategory.id == category_update.id)
    return CategoryVO.model_validate(await session.scalar(stmt))


@tag_api.post('/delete/{category_id}', response_model=int)
async def delete_tag(category_id: int) -> int:
    stmt = update(PostCategory).where(PostCategory.id == category_id).values(deleted=True)
    result = await session.execute(stmt)
    stmt = update(BlogPost).where(BlogPost.category_id == category_id).values(category_id=None)
    await session.execute(stmt)
    return result.rowcount
