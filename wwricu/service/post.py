from sqlalchemy import select

from wwricu.domain.entity import BlogPost
from wwricu.service.database import session


async def get_post_by_id(post_id: int) -> BlogPost:
    stmt = select(BlogPost).where(BlogPost.id == post_id).where(BlogPost.deleted == False)
    return await session.scalar(stmt)
