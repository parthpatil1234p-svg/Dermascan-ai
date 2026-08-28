from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.dependencies import get_products_collection, require_admin
from app.main import create_app
from app.schemas.product import ProductCreate
from app.schemas.user import UserPublic
from tests.catalogue_fakes import FakeCollection, demo_product


def product_payload(**overrides):
    document = demo_product()
    for key in (
        "_id",
        "normalized_product_name",
        "normalized_brand_name",
        "created_at",
        "updated_at",
    ):
        document.pop(key, None)
    document.update(overrides)
    for key in ("price_checked_at", "availability_checked_at", "source_verified_at"):
        if isinstance(document.get(key), datetime):
            document[key] = document[key].isoformat()
    return document


@pytest.mark.parametrize(
    "field,value",
    [
        ("product_name", " "),
        ("category", "medicine"),
        ("suitable_skin_types", ["unknown"]),
        ("target_visible_concerns", ["diagnosed_acne"]),
        ("price", {"amount": -1, "currency": "INR"}),
        ("price", {"amount": 100, "currency": "USD"}),
        ("country_codes", ["IND"]),
        ("availability_status", "everywhere"),
        ("official_product_url", "javascript:alert(1)"),
    ],
)
def test_reject_invalid_product_fields(field, value):
    with pytest.raises(ValidationError):
        ProductCreate.model_validate(product_payload(**{field: value}))


def test_demo_product_requires_demo_flag():
    with pytest.raises(ValidationError):
        ProductCreate.model_validate(product_payload(is_demo_product=False))


def test_valid_demo_product_contract():
    product = ProductCreate.model_validate(product_payload())
    assert product.product_name == "Test Gentle Cleanser"
    assert product.price and product.price.currency == "INR"


def create_client(products: FakeCollection):
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_products_collection] = lambda: products
    return TestClient(app)


def test_public_product_detail_is_safe_and_labelled():
    client = create_client(FakeCollection([demo_product()]))
    response = client.get("/api/products/PRD-TEST001")
    assert response.status_code == 200
    data = response.json()
    assert data["demo_label"].startswith("Demonstration Product")
    assert data["price_checked_at"]
    assert data["availability_checked_at"]
    assert "_id" not in data and "source_url" not in data


def test_missing_and_inactive_product_return_404():
    products = FakeCollection([demo_product(is_active=False)])
    client = create_client(products)
    assert client.get("/api/products/PRD-MISSING").status_code == 404
    assert client.get("/api/products/PRD-TEST001").status_code == 404


def test_draft_product_is_not_public():
    product = demo_product(data_type="unverified_draft", is_demo_product=False)
    client = create_client(FakeCollection([product]))
    assert client.get("/api/products/PRD-TEST001").status_code == 404


def test_admin_authorization_is_enforced():
    client = create_client(FakeCollection())
    response = client.post("/api/admin/products", json=product_payload())
    assert response.status_code == 401


def test_admin_create_and_soft_delete():
    products = FakeCollection()
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_products_collection] = lambda: products
    app.dependency_overrides[require_admin] = lambda: UserPublic(
        id="admin",
        full_name="Admin",
        email="admin@example.com",
        is_active=True,
        is_admin=True,
        created_at=datetime.now(timezone.utc),
    )
    client = TestClient(app)
    created = client.post("/api/admin/products", json=product_payload())
    assert created.status_code == 201
    deleted = client.delete("/api/admin/products/PRD-TEST001")
    assert deleted.status_code == 200
    assert client.get("/api/products/PRD-TEST001").status_code == 404
