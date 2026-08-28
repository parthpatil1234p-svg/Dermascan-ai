from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_brands_collection
from app.repositories.brand_repository import list_brands
from app.schemas.brand import BrandListResponse, brand_document_to_response
from app.schemas.pagination import pagination_metadata

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("", response_model=BrandListResponse)
async def read_brands(
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    collection=Depends(get_brands_collection),
) -> BrandListResponse:
    documents, total = await list_brands(collection, search, page, page_size)
    return BrandListResponse(
        items=[brand_document_to_response(document) for document in documents],
        pagination=pagination_metadata(page, page_size, total),
    )
