import pytest
from sqlalchemy import select

from wwricu.component.database import get_session
from wwricu.domain.entity import BlogPost
from wwricu.domain.enum import PostStatusEnum


@pytest.mark.asyncio
async def test_nested_get_session_same_transaction():
    post_ids = []

    async def create_post_1():
        async with get_session() as s:
            post = BlogPost(title="nested_post_1", status=PostStatusEnum.DRAFT)
            s.add(post)
            await s.flush()
            await s.refresh(post)
            post_ids.append(post.id)

    async def create_post_2_fail():
        async with get_session() as s:
            post = BlogPost(title="nested_post_2", status=PostStatusEnum.DRAFT)
            s.add(post)
            await s.flush()
            await s.refresh(post)
            post_ids.append(post.id)
            raise ValueError("Simulated failure in nested operation")

    async def create_post_3():
        async with get_session() as s:
            post = BlogPost(title="nested_post_3", status=PostStatusEnum.DRAFT)
            s.add(post)
            await s.flush()
            await s.refresh(post)
            post_ids.append(post.id)

    try:
        async with get_session():
            await create_post_1()
            await create_post_2_fail()
            await create_post_3()
    except ValueError:
        pass

    async with get_session() as session:
        for post_id in post_ids:
            result = await session.scalar(select(BlogPost).where(BlogPost.id == post_id))
            assert result is None, f"Post {post_id} should have been rolled back but exists"


@pytest.mark.asyncio
async def test_nested_get_session_commit_success():
    post_ids = []

    async def create_posts():
        async with get_session() as s:
            post1 = BlogPost(title="success_post_1", status=PostStatusEnum.DRAFT)
            s.add(post1)
            await s.flush()
            await s.refresh(post1)
            post_ids.append(post1.id)

        async with get_session() as s:
            post2 = BlogPost(title="success_post_2", status=PostStatusEnum.DRAFT)
            s.add(post2)
            await s.flush()
            await s.refresh(post2)
            post_ids.append(post2.id)

    async with get_session():
        await create_posts()

    async with get_session() as session:
        for post_id in post_ids:
            result = await session.scalar(select(BlogPost).where(BlogPost.id == post_id))
            assert result is not None, f"Post {post_id} should have been committed but missing"


@pytest.mark.asyncio
async def test_nested_get_session_partial_rollback():
    post1_id = None

    try:
        async with get_session():
            async with get_session() as inner_session1:
                post1 = BlogPost(title="partial_rollback_1", status=PostStatusEnum.DRAFT)
                inner_session1.add(post1)
                await inner_session1.flush()
                await inner_session1.refresh(post1)
                post1_id = post1.id

            async with get_session() as inner_session2:
                post2 = BlogPost(title="partial_rollback_2", status=PostStatusEnum.DRAFT)
                inner_session2.add(post2)
                await inner_session2.flush()
                raise ValueError("Inner operation failed")
    except ValueError:
        pass

    async with get_session() as session:
        result = await session.scalar(select(BlogPost).where(BlogPost.id == post1_id))
        assert result is None, "Post1 should have been rolled back due to inner failure"
