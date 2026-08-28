from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    auth,
    brands,
    face_detection,
    feedback,
    feedback_admin,
    final_reports,
    image_preprocessing,
    image_quality,
    ingredients,
    product_admin,
    product_eligibility,
    product_recommendations,
    products,
    report_exports,
    skin_concerns,
    skin_profiles,
    skin_type,
    skincare_routines,
    uploads,
    users,
)
from app.core.config import get_settings
from app.core.errors import (
    http_exception_handler,
    unexpected_exception_handler,
    validation_exception_handler,
)
from app.core.observability import configure_logging, register_operational_middleware
from app.database.mongodb import mongo_connection
from app.ml.model_registry import skin_type_model_registry
from app.ml.skin_concern_registry import skin_concern_model_registry
from app.services.face_crop_service import cleanup_expired_face_crops
from app.services.image_preprocessing_service import (
    cleanup_expired_preprocessed_images,
)
from app.services.readiness_service import build_readiness_report
from app.services.report_cleanup_service import cleanup_expired_report_exports
from app.services.upload_service import cleanup_expired_uploads
from app.utils.file_utils import ensure_directory


def create_app(enable_lifespan: bool = True) -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if enable_lifespan and not settings.is_testing:
            ensure_directory(settings.upload_path)
            ensure_directory(settings.face_crop_path)
            ensure_directory(settings.preprocessed_image_path)
            ensure_directory(settings.report_export_path)
            app.state.database = await mongo_connection.connect(settings)
            await cleanup_expired_uploads(
                app.state.database["image_uploads"],
                settings,
                app.state.database["image_quality_reports"],
                app.state.database["face_detection_reports"],
                app.state.database["image_preprocessing_reports"],
                app.state.database["skin_type_reports"],
                app.state.database["skin_concern_reports"],
            )
            await cleanup_expired_face_crops(app.state.database["face_detection_reports"], settings)
            await cleanup_expired_preprocessed_images(
                app.state.database["image_preprocessing_reports"], settings
            )
            cleanup_expired_report_exports(settings)
            skin_type_model_registry.initialize(settings)
            skin_concern_model_registry.initialize(settings)
        try:
            yield
        finally:
            if enable_lifespan and not settings.is_testing:
                await mongo_connection.close()

    app = FastAPI(
        title=settings.service_name,
        version="0.16.0",
        lifespan=lifespan,
    )

    register_operational_middleware(app, settings)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://dermascan-ai-eta.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ],
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    @app.get("/", tags=["health"])
    async def root_check() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name, "message": "Backend is running"}

    @app.get(f"{settings.api_prefix}/health", tags=["health"])
    async def health_check() -> dict[str, object]:
        return {
            "status": "healthy",
            "service": settings.service_name,
            "skin_type_model": skin_type_model_registry.status(),
            "skin_concern_model": skin_concern_model_registry.status(),
            "analysis_mode": "demonstration" if settings.ai_demo_mode else "model",
        }

    @app.get(f"{settings.api_prefix}/readiness", tags=["health"])
    async def readiness_check(request: Request) -> JSONResponse:
        report = await build_readiness_report(
            getattr(request.app.state, "database", None), settings
        )
        return JSONResponse(
            status_code=200 if report["status"] == "ready" else 503,
            content=report,
        )

    app.include_router(auth.router, prefix=settings.api_prefix)
    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(skin_profiles.router, prefix=settings.api_prefix)
    app.include_router(uploads.router, prefix=settings.api_prefix)
    app.include_router(image_quality.router, prefix=settings.api_prefix)
    app.include_router(face_detection.router, prefix=settings.api_prefix)
    app.include_router(image_preprocessing.router, prefix=settings.api_prefix)
    app.include_router(skin_type.router, prefix=settings.api_prefix)
    app.include_router(skin_concerns.router, prefix=settings.api_prefix)
    app.include_router(products.router, prefix=settings.api_prefix)
    app.include_router(brands.router, prefix=settings.api_prefix)
    app.include_router(ingredients.router, prefix=settings.api_prefix)
    app.include_router(product_admin.router, prefix=settings.api_prefix)
    app.include_router(product_eligibility.router, prefix=settings.api_prefix)
    app.include_router(product_recommendations.router, prefix=settings.api_prefix)
    app.include_router(skincare_routines.router, prefix=settings.api_prefix)
    app.include_router(final_reports.router, prefix=settings.api_prefix)
    app.include_router(report_exports.router, prefix=settings.api_prefix)
    app.include_router(feedback.router, prefix=settings.api_prefix)
    app.include_router(feedback_admin.router, prefix=settings.api_prefix)
    return app


app = create_app()
