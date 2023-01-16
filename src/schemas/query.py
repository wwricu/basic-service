from pydantic import BaseModel


class ResourceQuery(BaseModel):
    category_name: str = None
    tag_name: str = None
    page_idx: int = 0
    page_size: int = 0
