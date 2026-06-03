from sqlalchemy import select, update, func, desc, Select, literal_column, delete
from sqlalchemy.orm import defer, with_expression

from wwricu.component.database import get_session
from wwricu.domain.constant import CommonConst
from wwricu.domain.entity import BlogPost, EntityRelation, PostTag, BlogPostSearch
from wwricu.domain.enum import PostStatusEnum, RelationTypeEnum, TagTypeEnum
from wwricu.domain.post import PostQueryDTO


async def find_by_id(post_id: int) -> BlogPost | None:
    stmt = select(BlogPost).where(BlogPost.id == post_id).where(BlogPost.deleted == False)
    async with get_session() as s:
        return await s.scalar(stmt)


async def find_by_ids_by_tags(tag_names: list[str]) -> list[int]:
    if not tag_names:
        return []
    stmt = select(BlogPost.id).join(
        EntityRelation, BlogPost.id == EntityRelation.src_id).join(
        PostTag, PostTag.id == EntityRelation.dst_id).where(
        PostTag.deleted == False).where(
        EntityRelation.deleted == False).where(
        BlogPost.deleted == False).where(
        PostTag.type == TagTypeEnum.POST_TAG).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        PostTag.name.in_(tag_names)
    )
    async with get_session() as s:
        return list((await s.scalars(stmt)).all())


async def update_selective(post_id: int, **kwargs):
    stmt = update(BlogPost).where(BlogPost.id == post_id).where(BlogPost.deleted == False).values(**kwargs)
    async with get_session() as s:
        await s.execute(stmt)


async def find_published(post_id: int) -> BlogPost | None:
    stmt = select(BlogPost).where(
        BlogPost.id == post_id).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED
    )
    async with get_session() as s:
        return await s.scalar(stmt)


async def find_by_criteria(query: PostQueryDTO) -> list[BlogPost]:
    stmt = await build_criteria(query)
    stmt = stmt.order_by(desc(BlogPost.create_time))
    if query.page_size and query.page_size > 0 and query.page_index and query.page_index > 0:
        query.page_size = min(query.page_size, 100)
        stmt = stmt.limit(query.page_size).offset((query.page_index - 1) * query.page_size)
    async with get_session() as s:
        posts_result = await s.scalars(stmt)
    return list(posts_result.all())


async def count(query: PostQueryDTO) -> int:
    return await count_by_stmt(await build_criteria(query))


async def delete_tags(post_id: int):
    stmt = update(EntityRelation).where(
        EntityRelation.type == RelationTypeEnum.POST_TAG).where(
        EntityRelation.deleted == False).where(
        EntityRelation.src_id == post_id).values(
        deleted=True
    )
    async with get_session() as s:
        await s.execute(stmt)


async def upsert_search_index(post_id: int, title: str, preview: str, raw_content: str):
    async with get_session() as s:
        await s.execute(delete(BlogPostSearch).where(BlogPostSearch.rowid == post_id))
        s.add(BlogPostSearch(
            rowid=post_id,
            title=title,
            preview=preview,
            raw_content=raw_content,
        ))


async def search(keyword: str) -> list[BlogPost]:
    if not keyword or not keyword.strip():
        return []

    table = literal_column(BlogPostSearch.__tablename__)
    snippet_expr = func.snippet(table, 2, CommonConst.SNIPPET_MARKER, CommonConst.SNIPPET_MARKER, '…', 32)
    stmt = select(BlogPost).options(
        defer(BlogPost.content, raiseload=True),
        with_expression(BlogPost.snippet, snippet_expr),
    ).join(
        BlogPostSearch, BlogPost.id == BlogPostSearch.rowid).where(
        BlogPost.deleted == False).where(
        BlogPost.status == PostStatusEnum.PUBLISHED).where(
        table.match(keyword)
    ).order_by(func.bm25(table, 10.0, 5.0, 1.0)).limit(30)

    async with get_session() as session:
        posts = list((await session.scalars(stmt)).all())
    for p in posts:
        p.snippet = p.snippet.replace(CommonConst.SNIPPET_MARKER, '') if p.snippet and CommonConst.SNIPPET_MARKER in p.snippet else None
    return posts


async def count_by_stmt(stmt: Select) -> int:
    count_stmt = select(func.count()).select_from(stmt.subquery())
    async with get_session() as s:
        return await s.scalar(count_stmt) or 0


async def build_criteria(query: PostQueryDTO) -> Select:
    stmt = select(BlogPost).options(defer(BlogPost.content, raiseload=True))
    if query.status is not None:
        stmt = stmt.where(BlogPost.status == query.status.value)
    if query.deleted is not None:
        stmt = stmt.where(BlogPost.deleted == query.deleted)
    if query.category_id is not None:
        stmt = stmt.where(BlogPost.category_id == query.category_id)
    if query.post_ids is not None:
        stmt = stmt.where(BlogPost.id.in_(query.post_ids))
    return stmt
