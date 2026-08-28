from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_brands_collection,
    get_ingredients_collection,
    get_products_collection,
)
from app.main import create_app
from app.models.brand import build_brand_document
from app.models.ingredient import build_ingredient_document
from app.schemas.brand import BrandCreate
from app.schemas.ingredient import IngredientCreate
from app.schemas.product import ProductCreate
from app.services.ingredient_normalization_service import normalize_ingredient_names
from tests.catalogue_fakes import FakeCollection, demo_product
from tests.test_products import product_payload


def ingredient_document(identifier="ING-00003", name="Niacinamide", category="active"):
    now = datetime.now(timezone.utc)
    return build_ingredient_document(
        IngredientCreate(
            ingredient_id=identifier,
            canonical_name=name,
            aliases=["Vitamin B3", "Nicotinamide"] if name == "Niacinamide" else [],
            ingredient_category=category,
            common_skincare_roles=["barrier support"],
            caution_notes=["Individual tolerance may vary."],
        ),
        now,
    )


def client():
    ingredients = FakeCollection(
        [ingredient_document(), ingredient_document("ING-00002", "Glycerin", "humectant")]
    )
    products = FakeCollection([demo_product()])
    brands = FakeCollection(
        [
            build_brand_document(
                BrandCreate(brand_id="BRD-DEMO", brand_name="DermaDemo Labs"),
                datetime.now(timezone.utc),
            )
        ]
    )
    app = create_app(enable_lifespan=False)
    app.dependency_overrides[get_ingredients_collection] = lambda: ingredients
    app.dependency_overrides[get_products_collection] = lambda: products
    app.dependency_overrides[get_brands_collection] = lambda: brands
    return TestClient(app)


def test_normalize_aliases_to_exact_canonical_key():
    result = normalize_ingredient_names(
        ["Vitamin B3", "niacinamide", "Unmapped Extract"],
        {"vitamin b3": "niacinamide", "niacinamide": "niacinamide"},
    )
    assert result.normalized_ids == ["niacinamide"]
    assert result.unmapped == ["Unmapped Extract"]


def test_normalization_avoids_partial_string_matches():
    result = normalize_ingredient_names(["Niacin"], {"niacinamide": "niacinamide"})
    assert result.normalized_ids == [] and result.unmapped == ["Niacin"]


def test_ingredient_schema_removes_duplicate_aliases():
    ingredient = IngredientCreate(
        ingredient_id="ING-TEST",
        canonical_name=" Test Ingredient ",
        aliases=["Alias", " alias "],
        ingredient_category="other",
    )
    assert ingredient.canonical_name == "Test Ingredient"
    assert ingredient.aliases == ["Alias"]


def test_product_preserves_original_ingredient_order():
    payload = product_payload(
        ingredients=[
            {"display_name": "Water", "position": 1},
            {"display_name": "Glycerin", "position": 2},
        ]
    )
    product = ProductCreate.model_validate(payload)
    assert [item.display_name for item in product.ingredients] == ["Water", "Glycerin"]


def test_list_and_filter_ingredients():
    data = client().get("/api/ingredients?ingredient_category=active").json()
    assert data["pagination"]["total_items"] == 1
    assert data["items"][0]["canonical_name"] == "Niacinamide"


def test_search_ingredient_alias():
    data = client().get("/api/ingredients?search=Vitamin%20B3").json()
    assert data["items"][0]["ingredient_id"] == "ING-00003"


def test_ingredient_detail_lists_public_products_without_medical_advice():
    data = client().get("/api/ingredients/ING-00003").json()
    assert data["products"][0]["product_id"] == "PRD-TEST001"
    assert "not medical advice" in data["disclaimer"]


def test_brands_are_normalized_and_publicly_listed():
    data = client().get("/api/brands?search=dermademo").json()
    assert data["items"][0]["brand_name"] == "DermaDemo Labs"
