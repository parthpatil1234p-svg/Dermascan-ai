from fastapi.testclient import TestClient

from app.api.dependencies import get_products_collection
from app.main import create_app
from app.services.product_search_service import ProductFilters, build_product_query
from tests.catalogue_fakes import FakeCollection, demo_product, matches


def catalogue():
    return [
        demo_product(
            product_id="PRD-A001",
            slug="alpha-cleanser",
            product_name="Alpha Cleanser",
            price={"amount": 200, "currency": "INR"},
        ),
        demo_product(
            product_id="PRD-B002",
            slug="beta-serum",
            product_name="Beta Serum",
            category="serum",
            suitable_skin_types=["dry"],
            target_visible_concerns=["dark_spots"],
            normalized_ingredients=["glycerin"],
            highlighted_ingredients=["Glycerin"],
            price={"amount": 800, "currency": "INR"},
            fragrance_status="contains_added_fragrance",
        ),
        demo_product(
            product_id="PRD-C003",
            slug="gamma-cream",
            product_name="Gamma Cream",
            category="moisturizer",
            brand_id="BRD-BARRIERWORKS",
            brand_name="BarrierWorks",
            normalized_brand_name="barrierworks",
            country_codes=["GB"],
            availability_status="limited",
            price={"amount": 1200, "currency": "INR"},
        ),
        demo_product(
            product_id="PRD-D004",
            slug="draft-product",
            product_name="Draft Product",
            data_type="unverified_draft",
            is_demo_product=False,
        ),
        demo_product(
            product_id="PRD-E005",
            slug="inactive-product",
            product_name="Inactive Product",
            is_active=False,
        ),
    ]


def client():
    products = FakeCollection(catalogue())
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_products_collection] = lambda: products
    return TestClient(app)


def test_public_listing_excludes_drafts_and_inactive_products():
    data = client().get("/api/products").json()
    assert data["pagination"]["total_items"] == 3


def test_pagination_metadata_and_page_size():
    data = client().get("/api/products?page=2&page_size=2").json()
    assert len(data["items"]) == 1
    assert data["pagination"] == {
        "page": 2,
        "page_size": 2,
        "total_items": 3,
        "total_pages": 2,
        "has_next": False,
        "has_previous": True,
    }


def test_filter_by_category():
    data = client().get("/api/products?category=serum").json()
    assert [item["product_id"] for item in data["items"]] == ["PRD-B002"]


def test_filter_by_skin_type():
    data = client().get("/api/products?skin_type=dry").json()
    assert [item["product_id"] for item in data["items"]] == ["PRD-B002"]


def test_filter_by_visible_concern():
    data = client().get("/api/products?visible_concern=dark_spots").json()
    assert [item["product_id"] for item in data["items"]] == ["PRD-B002"]


def test_include_and_exclude_ingredient():
    included = client().get("/api/products?ingredient=niacinamide").json()
    excluded = client().get("/api/products?exclude_ingredient=niacinamide").json()
    assert included["pagination"]["total_items"] == 2
    assert {item["product_id"] for item in excluded["items"]} == {"PRD-B002"}


def test_filter_by_price_range():
    data = client().get("/api/products?min_price=300&max_price=900").json()
    assert [item["product_id"] for item in data["items"]] == ["PRD-B002"]


def test_reject_invalid_price_range():
    response = client().get("/api/products?min_price=900&max_price=300")
    assert response.status_code == 422
    assert response.json()["detail"].startswith("Maximum price")


def test_filter_by_country_and_availability():
    data = client().get("/api/products?country=GB&availability=limited").json()
    assert [item["product_id"] for item in data["items"]] == ["PRD-C003"]


def test_filter_by_fragrance_status():
    data = client().get("/api/products?fragrance_status=contains_added_fragrance").json()
    assert [item["product_id"] for item in data["items"]] == ["PRD-B002"]


def test_search_product_name():
    data = client().get("/api/products?search=Beta").json()
    assert [item["product_name"] for item in data["items"]] == ["Beta Serum"]


def test_search_brand():
    data = client().get("/api/products?search=BarrierWorks").json()
    assert [item["product_id"] for item in data["items"]] == ["PRD-C003"]


def test_sort_by_price():
    low = client().get("/api/products?sort=price_low_to_high").json()["items"]
    high = client().get("/api/products?sort=price_high_to_low").json()["items"]
    assert [item["product_id"] for item in low] == ["PRD-A001", "PRD-B002", "PRD-C003"]
    assert high[0]["product_id"] == "PRD-C003"


def test_invalid_controlled_filters_are_rejected():
    assert client().get("/api/products?category=medicine").status_code == 422
    assert client().get("/api/products?sort=best").status_code == 422


def test_query_uses_escaped_regex_not_user_operator():
    query = build_product_query(ProductFilters(search=".*"))
    assert not matches(catalogue()[0], query)
