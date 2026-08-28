from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.core.catalogue import PUBLIC_DATA_TYPES
from app.core.config import Settings
from app.models.product import normalize_key
from app.models.product_eligibility import build_eligibility_report_document
from app.repositories.product_eligibility_repository import (
    find_eligibility_report,
    upsert_eligibility_report,
)
from app.rules.availability_rules import COUNTRY_ALIASES
from app.rules.compatibility_rules import BASIC_CATEGORIES
from app.schemas.pagination import pagination_metadata
from app.schemas.product_eligibility import (
    EligibilityCandidateResponse,
    EligibilityReason,
    EligibilitySummary,
    FilteringBudget,
    FilteringSkinType,
    ProductEligibilityDetailResponse,
    ProductEligibilityReportResponse,
    StoredProductEligibilityResult,
    UserFilteringContext,
)
from app.services.age_filter_service import evaluate_age
from app.services.allergy_filter_service import evaluate_allergies, normalize_allergies
from app.services.availability_filter_service import evaluate_availability
from app.services.budget_filter_service import evaluate_budget
from app.services.ingredient_filter_service import (
    evaluate_avoided_ingredients,
    normalize_avoidances,
)
from app.services.product_data_quality_service import evaluate_product_data_quality
from app.services.product_service import product_summary
from app.services.sensitivity_filter_service import evaluate_fragrance, evaluate_sensitivity
from app.services.upload_service import get_owned_upload_document


class EligibilityUploadNotFoundError(Exception):
    pass


class EligibilityPrerequisiteError(Exception):
    pass


class EligibilityCatalogueEmptyError(Exception):
    pass


class EligibilityReportNotFoundError(Exception):
    pass


class EligibilityProductNotFoundError(Exception):
    pass


class EligibilityEvaluationError(Exception):
    pass


ELIGIBILITY_UPLOAD_STATUSES = {
    "skin_concern_analysis_completed",
    "skin_concern_analysis_uncertain",
    "product_discovery_pending",
    "product_eligibility_pending",
    "product_eligibility_completed",
    "product_eligibility_completed_with_gaps",
    "recommendation_scoring_pending",
    "product_eligibility_failed",
}

DISCLAIMER = (
    "Eligibility filtering uses self-reported information and available catalogue data. "
    "It cannot guarantee that a product will not cause irritation or an allergic response."
)


async def load_ingredient_lookup(collection: Any) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    async for document in collection.find({"is_active": True}):
        lookup[document["normalized_name"]] = document
        for alias in document.get("normalized_aliases", []):
            lookup[alias] = document
    return lookup


def normalize_country(value: str) -> str:
    key = normalize_key(value)
    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key]
    candidate = value.strip().upper()
    if len(candidate) == 2 and candidate.isalpha():
        return candidate
    raise EligibilityPrerequisiteError(
        "The skin profile country is not supported by the current catalogue."
    )


def build_user_filter_context(
    user_id: str,
    profile: dict[str, Any],
    skin_type_report: dict[str, Any],
    concern_report: dict[str, Any],
    ingredient_lookup: dict[str, dict[str, Any]],
    *,
    budget_mandatory: bool | None = None,
) -> UserFilteringContext:
    final_skin_type = skin_type_report.get("final_skin_type", "Uncertain")
    result_status = skin_type_report.get("result_status", "uncertain")
    is_uncertain = result_status == "uncertain" or normalize_key(final_skin_type) == "uncertain"
    concerns = list(
        dict.fromkeys(
            result["concern_code"]
            for result in concern_report.get("concern_results", [])
            if result.get("status") in {"observed", "possible"}
        )
    )
    preference_map = {
        "Fragrance-free only": "fragrance_free_only",
        "Prefer fragrance-free": "prefer_fragrance_free",
        "No preference": "no_preference",
    }
    has_budget = profile.get("budget_min") is not None and profile.get("budget_max") is not None
    return UserFilteringContext(
        user_id=user_id,
        age_group=profile["age_group"],
        country=normalize_country(profile["country"]),
        skin_type=FilteringSkinType(
            value="uncertain" if is_uncertain else normalize_key(final_skin_type),
            status="uncertain" if is_uncertain else "estimated",
            confidence=float(skin_type_report.get("model_confidence", 0)),
        ),
        visible_concerns=concerns,
        self_reported_sensitivity=profile.get("is_sensitive"),
        known_allergies=normalize_allergies(profile.get("known_allergies", []), ingredient_lookup),
        ingredients_to_avoid=normalize_avoidances(
            profile.get("ingredients_to_avoid", []), ingredient_lookup
        ),
        fragrance_preference=preference_map[profile["fragrance_preference"]],
        budget=FilteringBudget(
            minimum=profile.get("budget_min"),
            maximum=profile.get("budget_max"),
            currency="INR",
            mandatory=has_budget if budget_mandatory is None else budget_mandatory,
        ),
        preferred_brands=[normalize_key(value) for value in profile.get("preferred_brands", [])],
    )


def _extend_unique(target: list[EligibilityReason], values: list[EligibilityReason]) -> None:
    seen = {(item.code, item.matched_value) for item in target}
    for value in values:
        marker = (value.code, value.matched_value)
        if marker not in seen:
            target.append(value)
            seen.add(marker)


def evaluate_compatibility(product: dict[str, Any], context: UserFilteringContext):
    cautions: list[EligibilityReason] = []
    positives: list[EligibilityReason] = []
    skin_types = set(product.get("suitable_skin_types", []))
    if context.skin_type.status == "uncertain":
        cautions.append(
            EligibilityReason(
                code="SKIN_TYPE_PARTIAL_MATCH",
                message="Skin type is uncertain, so this product was not hard-filtered by one image-derived class.",
            )
        )
    elif context.skin_type.value in skin_types or "all_skin_types" in skin_types:
        positives.append(
            EligibilityReason(
                code="SKIN_TYPE_MATCH",
                message=f"The product is catalogued for {context.skin_type.value} skin.",
                matched_value=context.skin_type.value,
            )
        )
    else:
        cautions.append(
            EligibilityReason(
                code="SKIN_TYPE_MISMATCH",
                message="The catalogue does not list an exact match for the estimated skin type; this alone is not a medical exclusion.",
            )
        )
    matched_concerns = sorted(
        set(product.get("target_visible_concerns", [])) & set(context.visible_concerns)
    )
    if matched_concerns:
        positives.append(
            EligibilityReason(
                code="VISIBLE_CONCERN_MATCH",
                message="The product is mapped to at least one recorded visible skincare goal.",
                matched_value=", ".join(matched_concerns),
            )
        )
    elif product.get("category") not in BASIC_CATEGORIES:
        cautions.append(
            EligibilityReason(
                code="NO_VISIBLE_CONCERN_MATCH",
                message="This product has no direct mapping to the recorded visible skincare goals.",
            )
        )
    return cautions, positives


def evaluate_product(
    product: dict[str, Any],
    context: UserFilteringContext,
    ingredient_lookup: dict[str, dict[str, Any]],
    settings: Settings,
) -> StoredProductEligibilityResult:
    hard: list[EligibilityReason] = []
    cautions: list[EligibilityReason] = []
    positives: list[EligibilityReason] = []
    gaps: list[EligibilityReason] = []

    quality_hard, quality_cautions, quality_gaps = evaluate_product_data_quality(
        product, context, settings
    )
    _extend_unique(hard, quality_hard)
    _extend_unique(cautions, quality_cautions)
    _extend_unique(gaps, quality_gaps)
    allergy_hard, allergy_cautions = evaluate_allergies(
        product, context.known_allergies, ingredient_lookup
    )
    _extend_unique(hard, allergy_hard)
    _extend_unique(cautions, allergy_cautions)
    avoided_hard, avoided_cautions = evaluate_avoided_ingredients(
        product, context.ingredients_to_avoid, ingredient_lookup
    )
    _extend_unique(hard, avoided_hard)
    _extend_unique(cautions, avoided_cautions)
    _extend_unique(hard, evaluate_age(product, context.age_group))

    availability_hard, availability_cautions, availability_positive, availability_gaps = (
        evaluate_availability(product, context.country, settings)
    )
    _extend_unique(hard, availability_hard)
    _extend_unique(cautions, availability_cautions)
    _extend_unique(positives, availability_positive)
    _extend_unique(gaps, availability_gaps)
    budget_hard, budget_cautions, budget_positive, budget_gaps = evaluate_budget(
        product, context.budget, settings
    )
    _extend_unique(hard, budget_hard)
    _extend_unique(cautions, budget_cautions)
    _extend_unique(positives, budget_positive)
    _extend_unique(gaps, budget_gaps)

    sensitivity_cautions, sensitivity_positive = evaluate_sensitivity(
        product, context.self_reported_sensitivity
    )
    _extend_unique(cautions, sensitivity_cautions)
    _extend_unique(positives, sensitivity_positive)
    fragrance_hard, fragrance_cautions, fragrance_gaps = evaluate_fragrance(
        product, context.fragrance_preference
    )
    _extend_unique(hard, fragrance_hard)
    _extend_unique(cautions, fragrance_cautions)
    _extend_unique(gaps, fragrance_gaps)
    compatibility_cautions, compatibility_positive = evaluate_compatibility(product, context)
    _extend_unique(cautions, compatibility_cautions)
    _extend_unique(positives, compatibility_positive)

    status = (
        "excluded"
        if hard
        else (
            "insufficient_information"
            if gaps
            else "eligible_with_caution" if cautions else "eligible"
        )
    )
    return StoredProductEligibilityResult(
        product_id=product["product_id"],
        product_name=product["product_name"],
        brand_name=product["brand_name"],
        category=product.get("category", "unknown"),
        is_demo_product=bool(product.get("is_demo_product")),
        price=product.get("price"),
        price_checked_at=product.get("price_checked_at"),
        availability_status=product.get("availability_status", "unknown"),
        availability_checked_at=product.get("availability_checked_at"),
        eligibility_status=status,
        hard_exclusions=hard,
        cautions=cautions,
        positive_matches=positives,
        information_gaps=gaps,
    )


async def _set_upload_status(collection: Any, upload: dict[str, Any], value: str) -> None:
    await collection.update_one(
        {"_id": upload["_id"]},
        {"$set": {"status": value, "updated_at": datetime.now(timezone.utc)}},
    )


async def evaluate_owned_catalogue(
    *,
    upload_id: str,
    user_id: str,
    uploads: Any,
    profiles: Any,
    skin_types: Any,
    concerns: Any,
    products: Any,
    ingredients: Any,
    reports: Any,
    settings: Settings,
    user_avoidances: Any | None = None,
) -> dict[str, Any]:
    upload = await get_owned_upload_document(uploads, upload_id, user_id)
    if upload is None:
        raise EligibilityUploadNotFoundError
    if upload.get("status") == "product_eligibility_evaluating":
        raise EligibilityPrerequisiteError("Product eligibility evaluation is already running.")
    if upload.get("status") not in ELIGIBILITY_UPLOAD_STATUSES:
        raise EligibilityPrerequisiteError(
            "Complete visible skin-concern analysis before product filtering."
        )
    owner = ObjectId(user_id)
    profile = await profiles.find_one({"user_id": owner})
    skin_type = await skin_types.find_one({"upload_id": upload_id, "user_id": owner})
    concern = await concerns.find_one({"upload_id": upload_id, "user_id": owner})
    if profile is None or not profile.get("is_complete"):
        raise EligibilityPrerequisiteError("Complete your skin profile before product filtering.")
    if skin_type is None or skin_type.get("result_status") not in {"estimated", "uncertain"}:
        raise EligibilityPrerequisiteError("Complete skin-type analysis before product filtering.")
    if concern is None or concern.get("overall_status") not in {
        "completed",
        "completed_with_uncertainty",
    }:
        raise EligibilityPrerequisiteError(
            "Complete visible skin-concern analysis before product filtering."
        )
    catalogue = await products.find(
        {"is_active": True, "data_type": {"$in": list(PUBLIC_DATA_TYPES)}}
    ).to_list(length=None)
    if not catalogue:
        raise EligibilityCatalogueEmptyError
    lookup = await load_ingredient_lookup(ingredients)
    context = build_user_filter_context(user_id, profile, skin_type, concern, lookup)
    await _set_upload_status(uploads, upload, "product_eligibility_evaluating")
    try:
        avoided_ids: set[str] = set()
        if user_avoidances is not None:
            avoided = await user_avoidances.find({"user_id": owner, "is_active": True}).to_list(
                length=None
            )
            avoided_ids = {item["product_id"] for item in avoided}
        results = []
        for product in catalogue:
            result = evaluate_product(product, context, lookup, settings)
            if product["product_id"] in avoided_ids:
                avoidance = EligibilityReason(
                    code="USER_REPORTED_PRODUCT_AVOIDANCE",
                    message=(
                        "You previously asked to exclude this product after reporting "
                        "discomfort or irritation. This is a private preference signal, not a verified allergy."
                    ),
                    matched_value=product["product_id"],
                )
                result = result.model_copy(
                    update={
                        "eligibility_status": "excluded",
                        "hard_exclusions": [avoidance, *result.hard_exclusions],
                    }
                )
            results.append(result)
        existing = await find_eligibility_report(reports, upload_id, user_id)
        document = build_eligibility_report_document(
            upload_id=upload_id,
            user_id=user_id,
            skin_profile=profile,
            skin_type_report=skin_type,
            concern_report=concern,
            context=context,
            results=results,
            now=datetime.now(timezone.utc),
            existing=existing,
        )
        await upsert_eligibility_report(reports, document)
        await _set_upload_status(uploads, upload, "recommendation_scoring_pending")
        return document
    except Exception as exc:
        await _set_upload_status(uploads, upload, "product_eligibility_failed")
        if isinstance(exc, (EligibilityPrerequisiteError, EligibilityCatalogueEmptyError)):
            raise
        raise EligibilityEvaluationError from exc


def report_response(
    document: dict[str, Any],
    *,
    status: str | None = None,
    category: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> ProductEligibilityReportResponse:
    results = [
        StoredProductEligibilityResult.model_validate(item) for item in document["product_results"]
    ]
    status_order = {
        "eligible": 0,
        "eligible_with_caution": 1,
        "insufficient_information": 2,
        "excluded": 3,
    }
    results.sort(
        key=lambda item: (status_order[item.eligibility_status], item.product_name.casefold())
    )
    if status:
        results = [item for item in results if item.eligibility_status == status]
    if category:
        results = [item for item in results if item.category == category]
    total = len(results)
    page_items = results[(page - 1) * page_size : page * page_size]
    candidates = [
        EligibilityCandidateResponse(
            product_id=item.product_id,
            product_name=item.product_name,
            brand_name=item.brand_name,
            category=item.category,
            is_demo_product=item.is_demo_product,
            demo_label="Demonstration Product" if item.is_demo_product else None,
            price=item.price,
            price_checked_at=item.price_checked_at,
            availability_status=item.availability_status,
            availability_checked_at=item.availability_checked_at,
            eligibility_status=item.eligibility_status,
            positive_match_count=len(item.positive_matches),
            caution_count=len(item.cautions),
            exclusion_count=len(item.hard_exclusions),
            information_gap_count=len(item.information_gaps),
            primary_reasons=(
                item.hard_exclusions
                or item.information_gaps
                or item.cautions
                or item.positive_matches
            )[:3],
        )
        for item in page_items
    ]
    summary = EligibilitySummary(
        total_evaluated=document["total_products_evaluated"],
        eligible=document["eligible_count"],
        eligible_with_caution=document["eligible_with_caution_count"],
        excluded=document["excluded_count"],
        insufficient_information=document["insufficient_information_count"],
    )
    return ProductEligibilityReportResponse(
        eligibility_report_id=document["eligibility_report_id"],
        upload_id=document["upload_id"],
        summary=summary,
        candidate_products=candidates,
        pagination=pagination_metadata(page, page_size, total),
        can_continue=(summary.eligible + summary.eligible_with_caution) > 0,
        next_route="/product-recommendations",
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


async def get_owned_report(reports: Any, upload_id: str, user_id: str) -> dict[str, Any]:
    document = await find_eligibility_report(reports, upload_id, user_id)
    if document is None:
        raise EligibilityReportNotFoundError
    return document


async def get_owned_product_detail(
    reports: Any,
    products: Any,
    upload_id: str,
    product_id: str,
    user_id: str,
    settings: Settings,
) -> ProductEligibilityDetailResponse:
    report = await get_owned_report(reports, upload_id, user_id)
    result_data = next(
        (item for item in report["product_results"] if item["product_id"] == product_id), None
    )
    if result_data is None:
        raise EligibilityProductNotFoundError
    product = await products.find_one({"product_id": product_id})
    if product is None:
        raise EligibilityProductNotFoundError
    result = StoredProductEligibilityResult.model_validate(result_data)
    return ProductEligibilityDetailResponse(
        upload_id=upload_id,
        product=product_summary(product, settings),
        eligibility_status=result.eligibility_status,
        hard_exclusions=result.hard_exclusions,
        cautions=result.cautions,
        positive_matches=result.positive_matches,
        information_gaps=result.information_gaps,
        disclaimer=DISCLAIMER,
    )
