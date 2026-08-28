from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from app.core.config import Settings
from app.models.product import normalize_key
from app.models.product_recommendation import (
    REPORT_LIMITATIONS,
    build_recommendation_report_document,
)
from app.repositories.product_eligibility_repository import find_eligibility_report
from app.repositories.recommendation_repository import (
    find_recommendation_report,
    upsert_recommendation_report,
)
from app.rules.category_rules import CATEGORY_ORDER, CORE_RECOMMENDATION_CATEGORIES
from app.rules.caution_penalties import get_penalty_configuration
from app.rules.diversity_rules import price_tier
from app.rules.scoring_weights import SCORING_CONFIGURATION_VERSION, get_scoring_weights
from app.schemas.pagination import pagination_metadata
from app.schemas.product_eligibility import (
    FilteringBudget,
    FilteringSkinType,
    StoredProductEligibilityResult,
)
from app.schemas.product_recommendation import (
    ProductRecommendationDetailResponse,
    ProductRecommendationReportResponse,
    RecommendationCandidate,
    RecommendationContext,
    RecommendationProductResponse,
    RecommendationScoreBreakdown,
    StoredRecommendation,
)
from app.services.product_service import product_summary
from app.services.recommendation_confidence_service import (
    calculate_overall_confidence,
    calculate_recommendation_confidence,
)
from app.services.recommendation_explanation_service import build_recommendation_explanation
from app.services.recommendation_scoring_service import (
    calculate_score_breakdown,
    score_band,
)
from app.services.recommendation_selection_service import select_recommendations, sort_candidates
from app.services.upload_service import get_owned_upload_document


class RecommendationUploadNotFoundError(Exception):
    pass


class RecommendationPrerequisiteError(Exception):
    pass


class RecommendationReportNotFoundError(Exception):
    pass


class RecommendationProductNotFoundError(Exception):
    pass


class RecommendationGenerationError(Exception):
    pass


RECOMMENDATION_UPLOAD_STATUSES = {
    "recommendation_scoring_pending",
    "recommendations_completed",
    "recommendations_completed_with_limitations",
    "routine_generation_pending",
    "recommendations_failed",
}

DISCLAIMER = (
    "Recommendation scores are project-specific catalogue relevance scores. "
    "They are not medical scores and do not guarantee safety or effectiveness."
)


async def load_ingredient_roles(collection: Any) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    async for document in collection.find({"is_active": True}):
        roles = list(document.get("common_skincare_roles", []))
        lookup[document["normalized_name"]] = roles
        for alias in document.get("normalized_aliases", []):
            lookup[alias] = roles
    return lookup


def build_recommendation_context(
    eligibility_report: dict[str, Any],
    profile: dict[str, Any],
    concern_report: dict[str, Any],
) -> RecommendationContext:
    stored = eligibility_report["user_filter_context"]
    concerns = {
        result["concern_code"]: result.get("status", "uncertain")
        for result in concern_report.get("concern_results", [])
        if result.get("status") in {"observed", "possible", "uncertain", "not_observed"}
    }
    return RecommendationContext(
        skin_type=FilteringSkinType.model_validate(stored["skin_type"]),
        concerns=concerns,
        self_reported_sensitivity=stored.get("self_reported_sensitivity"),
        oiliness_level=profile.get("oiliness_level", "Not sure"),
        dryness_level=profile.get("dryness_level", "Not sure"),
        country=stored["country"],
        budget=FilteringBudget.model_validate(stored["budget"]),
        preferred_brands=list(stored.get("preferred_brands", [])),
    )


def build_candidate(
    product: dict[str, Any],
    eligibility: StoredProductEligibilityResult,
    ingredient_roles: dict[str, list[str]],
) -> RecommendationCandidate:
    roles: list[str] = []
    for ingredient in product.get("normalized_ingredients", []):
        roles.extend(ingredient_roles.get(ingredient, []))
    return RecommendationCandidate(
        product_id=product["product_id"],
        product_name=product["product_name"],
        brand_name=product["brand_name"],
        normalized_brand_name=product.get(
            "normalized_brand_name", normalize_key(product["brand_name"])
        ),
        category=product["category"],
        eligibility_status=eligibility.eligibility_status,
        is_demo_product=bool(product.get("is_demo_product")),
        data_type=product.get("data_type", "unverified_draft"),
        suitable_skin_types=product.get("suitable_skin_types", []),
        target_visible_concerns=product.get("target_visible_concerns", []),
        normalized_ingredients=product.get("normalized_ingredients", []),
        highlighted_ingredients=product.get("highlighted_ingredients", []),
        ingredient_roles=list(dict.fromkeys(roles)),
        sensitivity_suitability=product.get("sensitivity_suitability", "unknown"),
        fragrance_status=product.get("fragrance_status", "unknown"),
        price=product.get("price"),
        price_checked_at=product.get("price_checked_at"),
        country_codes=product.get("country_codes", []),
        availability_status=product.get("availability_status", "unknown"),
        availability_checked_at=product.get("availability_checked_at"),
        source_verified_at=product.get("source_verified_at"),
        rating=product.get("rating"),
        cautions=eligibility.cautions,
        positive_matches=eligibility.positive_matches,
    )


def score_candidate(
    candidate: RecommendationCandidate,
    context: RecommendationContext,
    settings: Settings,
    *,
    score_gap: float = 0,
) -> StoredRecommendation:
    breakdown, penalties, freshness = calculate_score_breakdown(candidate, context, settings)
    band = score_band(breakdown.final_score)
    why, positives, cautions = build_recommendation_explanation(
        candidate, context, breakdown, penalties, band
    )
    confidence, confidence_reasons = calculate_recommendation_confidence(
        candidate, context, breakdown, freshness, score_gap=score_gap
    )
    return StoredRecommendation(
        product_id=candidate.product_id,
        product_name=candidate.product_name,
        brand_name=candidate.brand_name,
        normalized_brand_name=candidate.normalized_brand_name,
        category=candidate.category,
        is_demo_product=candidate.is_demo_product,
        price=candidate.price,
        availability_status=candidate.availability_status,
        eligibility_status=candidate.eligibility_status,
        base_score=breakdown.base_score,
        penalties=penalties,
        total_penalty=breakdown.caution_penalty,
        final_score=breakdown.final_score,
        score_band=band,
        score_breakdown=breakdown,
        positive_factors=positives,
        caution_factors=cautions,
        why_recommended=why,
        recommendation_confidence=confidence,
        confidence_reasons=confidence_reasons,
        data_freshness=freshness,
        ingredient_profile=sorted(candidate.normalized_ingredients),
        price_tier=price_tier(candidate.price),
    )


def apply_score_separation_confidence(
    scored: list[StoredRecommendation],
    candidates: dict[str, RecommendationCandidate],
    context: RecommendationContext,
) -> list[StoredRecommendation]:
    output: list[StoredRecommendation] = []
    for category in CATEGORY_ORDER:
        category_items = sort_candidates([item for item in scored if item.category == category])
        for index, item in enumerate(category_items):
            next_score = (
                category_items[index + 1].final_score if index + 1 < len(category_items) else 0.0
            )
            confidence, reasons = calculate_recommendation_confidence(
                candidates[item.product_id],
                context,
                item.score_breakdown,
                item.data_freshness,
                score_gap=item.final_score - next_score,
            )
            output.append(
                item.model_copy(
                    update={
                        "recommendation_confidence": confidence,
                        "confidence_reasons": reasons,
                    }
                )
            )
    return output


def scoring_configuration(settings: Settings) -> dict[str, Any]:
    return {
        "version": SCORING_CONFIGURATION_VERSION,
        "weights": get_scoring_weights(settings),
        "penalties": get_penalty_configuration(settings),
        "minimum_display_score": settings.recommendation_min_display_score,
        "maximum_per_category": settings.recommendation_max_per_category,
        "maximum_same_brand": settings.recommendation_max_same_brand,
    }


async def _set_upload_status(collection: Any, upload: dict[str, Any], status: str) -> None:
    await collection.update_one(
        {"_id": upload["_id"]},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
    )


async def generate_owned_recommendations(
    *,
    upload_id: str,
    user_id: str,
    uploads: Any,
    eligibility_reports: Any,
    recommendation_reports: Any,
    products: Any,
    ingredients: Any,
    profiles: Any,
    concerns: Any,
    settings: Settings,
) -> dict[str, Any]:
    upload = await get_owned_upload_document(uploads, upload_id, user_id)
    if upload is None:
        raise RecommendationUploadNotFoundError
    if upload.get("status") == "recommendation_scoring":
        raise RecommendationPrerequisiteError("Recommendation generation is already running.")
    if upload.get("status") not in RECOMMENDATION_UPLOAD_STATUSES:
        raise RecommendationPrerequisiteError(
            "Complete product eligibility filtering before generating recommendations."
        )
    eligibility_report = await find_eligibility_report(eligibility_reports, upload_id, user_id)
    if eligibility_report is None:
        raise RecommendationPrerequisiteError(
            "Complete product eligibility filtering before generating recommendations."
        )
    owner = ObjectId(user_id)
    profile = await profiles.find_one({"user_id": owner})
    concern = await concerns.find_one({"upload_id": upload_id, "user_id": owner})
    if profile is None or not profile.get("is_complete") or concern is None:
        raise RecommendationPrerequisiteError(
            "Required profile or analysis context is unavailable."
        )

    eligible_results = [
        StoredProductEligibilityResult.model_validate(item)
        for item in eligibility_report.get("product_results", [])
        if item.get("eligibility_status") in {"eligible", "eligible_with_caution"}
    ]
    eligible_ids = [item.product_id for item in eligible_results]
    product_documents = await products.find(
        {
            "product_id": {"$in": eligible_ids},
            "is_active": True,
        }
    ).to_list(length=None)
    product_by_id = {item["product_id"]: item for item in product_documents}
    role_lookup = await load_ingredient_roles(ingredients)
    context = build_recommendation_context(eligibility_report, profile, concern)
    await _set_upload_status(uploads, upload, "recommendation_scoring")
    try:
        candidates = [
            build_candidate(product_by_id[result.product_id], result, role_lookup)
            for result in eligible_results
            if result.product_id in product_by_id
        ]
        candidate_by_id = {item.product_id: item for item in candidates}
        scored = [score_candidate(item, context, settings) for item in candidates]
        scored = apply_score_separation_confidence(scored, candidate_by_id, context)
        selected = select_recommendations(scored, settings)
        overall_confidence, confidence_reasons = calculate_overall_confidence(selected, context)
        existing = await find_recommendation_report(recommendation_reports, upload_id, user_id)
        document = build_recommendation_report_document(
            upload_id=upload_id,
            user_id=user_id,
            eligibility_report=eligibility_report,
            configuration=scoring_configuration(settings),
            candidate_results=scored,
            recommendations=selected,
            overall_confidence=overall_confidence,
            confidence_reasons=confidence_reasons,
            now=datetime.now(timezone.utc),
            existing=existing,
        )
        await upsert_recommendation_report(recommendation_reports, document)
        await _set_upload_status(uploads, upload, "routine_generation_pending")
        return document
    except Exception as exc:
        await _set_upload_status(uploads, upload, "recommendations_failed")
        raise RecommendationGenerationError from exc


def _rounded_breakdown(value: RecommendationScoreBreakdown) -> RecommendationScoreBreakdown:
    return RecommendationScoreBreakdown(
        **{key: round(number, 2) for key, number in value.model_dump().items()}
    )


def recommendation_to_public(item: StoredRecommendation) -> RecommendationProductResponse:
    return RecommendationProductResponse(
        rank=item.rank_within_category or 0,
        overall_rank=item.overall_rank or 0,
        product_id=item.product_id,
        product_name=item.product_name,
        brand_name=item.brand_name,
        category=item.category,
        is_demo_product=item.is_demo_product,
        demo_label="Demonstration Product" if item.is_demo_product else None,
        price=item.price,
        availability_status=item.availability_status,
        eligibility_status=item.eligibility_status,
        base_score=round(item.base_score, 2),
        caution_penalty=round(item.total_penalty, 2),
        final_score=round(item.final_score, 2),
        score_band=item.score_band,
        why_recommended=item.why_recommended,
        positive_factors=item.positive_factors,
        caution_factors=item.caution_factors,
        score_breakdown=_rounded_breakdown(item.score_breakdown),
        applied_penalties=[
            penalty.model_copy(update={"amount": round(penalty.amount, 2)})
            for penalty in item.penalties
        ],
        recommendation_confidence=item.recommendation_confidence,
        confidence_reasons=item.confidence_reasons,
        data_freshness=item.data_freshness,
    )


def recommendation_report_response(
    document: dict[str, Any],
    *,
    category: str | None = None,
    minimum_score: float = 0,
    page: int = 1,
    page_size: int = 20,
) -> ProductRecommendationReportResponse:
    items = [StoredRecommendation.model_validate(item) for item in document["recommendations"]]
    items = [item for item in items if item.final_score >= minimum_score]
    if category:
        items = [item for item in items if item.category == category]
    items.sort(key=lambda item: item.overall_rank or 10_000)
    total = len(items)
    page_items = items[(page - 1) * page_size : page * page_size]
    categories: dict[str, list[RecommendationProductResponse]] = {
        value: [] for value in CORE_RECOMMENDATION_CATEGORIES
    }
    for item in page_items:
        categories.setdefault(item.category, []).append(recommendation_to_public(item))
    return ProductRecommendationReportResponse(
        recommendation_report_id=document["recommendation_report_id"],
        upload_id=document["upload_id"],
        overall_confidence=document["overall_confidence"],
        confidence_reasons=document["confidence_reasons"],
        categories=categories,
        limitations=document.get("limitations", REPORT_LIMITATIONS),
        candidate_count=document["candidate_count"],
        recommended_count=document["recommended_count"],
        pagination=pagination_metadata(page, page_size, total),
        can_continue=document["recommended_count"] > 0,
        next_route="/skincare-routine",
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )


async def get_owned_recommendation_report(
    collection: Any,
    upload_id: str,
    user_id: str,
) -> dict[str, Any]:
    document = await find_recommendation_report(collection, upload_id, user_id)
    if document is None:
        raise RecommendationReportNotFoundError
    return document


async def get_owned_recommendation_detail(
    reports: Any,
    products: Any,
    upload_id: str,
    product_id: str,
    user_id: str,
    settings: Settings,
) -> ProductRecommendationDetailResponse:
    document = await get_owned_recommendation_report(reports, upload_id, user_id)
    stored = next(
        (item for item in document["recommendations"] if item["product_id"] == product_id),
        None,
    )
    if stored is None:
        raise RecommendationProductNotFoundError
    product = await products.find_one({"product_id": product_id, "is_active": True})
    if product is None:
        raise RecommendationProductNotFoundError
    return ProductRecommendationDetailResponse(
        upload_id=upload_id,
        product=product_summary(product, settings),
        recommendation=recommendation_to_public(StoredRecommendation.model_validate(stored)),
        disclaimer=DISCLAIMER,
    )
