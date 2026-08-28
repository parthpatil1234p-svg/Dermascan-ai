from math import ceil

from pydantic import BaseModel, Field


class PaginationMetadata(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool


def pagination_metadata(page: int, page_size: int, total_items: int) -> PaginationMetadata:
    total_pages = ceil(total_items / page_size) if total_items else 0
    return PaginationMetadata(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )
