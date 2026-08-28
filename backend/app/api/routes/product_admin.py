from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.dependencies import (
    get_product_import_jobs_collection,
    get_products_collection,
    require_admin,
)
from app.core.config import Settings, get_settings
from app.schemas.product import (
    ProductCreate,
    ProductDetailResponse,
    ProductImportResponse,
    ProductPatch,
)
from app.schemas.user import UserPublic
from app.services.catalogue_statistics_service import catalogue_statistics
from app.services.product_import_service import (
    ProductImportFormatError,
    import_product_records,
    parse_import_content,
)
from app.services.product_service import (
    ProductNotFoundError,
    create_catalogue_product,
    patch_catalogue_product,
    replace_catalogue_product,
    soft_delete_product,
)
from app.services.product_validation_service import DuplicateProductError

router = APIRouter(prefix="/admin/products", tags=["product catalogue administration"])


def catalogue_error(error: Exception) -> None:
    if isinstance(error, ProductNotFoundError):
        raise HTTPException(status_code=404, detail="Product not found.") from error
    if isinstance(error, DuplicateProductError):
        raise HTTPException(
            status_code=409, detail="A potential duplicate product already exists."
        ) from error
    raise error


@router.post("", response_model=ProductDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_products_collection),
    settings: Settings = Depends(get_settings),
) -> ProductDetailResponse:
    try:
        return await create_catalogue_product(collection, payload, settings)
    except Exception as error:
        catalogue_error(error)


@router.put("/{product_id}", response_model=ProductDetailResponse)
async def replace_product(
    product_id: str,
    payload: ProductCreate,
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_products_collection),
    settings: Settings = Depends(get_settings),
) -> ProductDetailResponse:
    if payload.product_id != product_id:
        raise HTTPException(status_code=422, detail="Product ID cannot be changed.")
    try:
        return await replace_catalogue_product(collection, product_id, payload, settings)
    except Exception as error:
        catalogue_error(error)


@router.patch("/{product_id}", response_model=ProductDetailResponse)
async def patch_product(
    product_id: str,
    payload: ProductPatch,
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_products_collection),
    settings: Settings = Depends(get_settings),
) -> ProductDetailResponse:
    try:
        return await patch_catalogue_product(collection, product_id, payload, settings)
    except Exception as error:
        catalogue_error(error)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_products_collection),
) -> dict[str, str]:
    try:
        await soft_delete_product(collection, product_id)
    except Exception as error:
        catalogue_error(error)
    return {"message": "Product deactivated successfully."}


@router.post("/import", response_model=ProductImportResponse)
async def import_products(
    file: UploadFile = File(...),
    dry_run: bool = Query(True),
    _: UserPublic = Depends(require_admin),
    products=Depends(get_products_collection),
    jobs=Depends(get_product_import_jobs_collection),
) -> ProductImportResponse:
    suffix = (file.filename or "").rsplit(".", 1)[-1].lower()
    try:
        records = parse_import_content(await file.read(), suffix)
        return await import_product_records(
            records, file.filename or f"import.{suffix}", suffix, products, jobs, dry_run=dry_run
        )
    except ProductImportFormatError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/import/{import_job_id}")
async def get_import_job(
    import_job_id: str,
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_product_import_jobs_collection),
) -> dict:
    document = await collection.find_one({"import_job_id": import_job_id})
    if document is None:
        raise HTTPException(status_code=404, detail="Import job not found.")
    document.pop("_id", None)
    return document


@router.get("/statistics/summary")
async def get_statistics(
    _: UserPublic = Depends(require_admin),
    collection=Depends(get_products_collection),
    settings: Settings = Depends(get_settings),
) -> dict:
    return await catalogue_statistics(collection, settings)
