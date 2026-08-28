from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(..., alias="APP_NAME")
    app_env: str = Field("development", alias="APP_ENV")
    api_prefix: str = Field("/api", alias="API_PREFIX")
    mongodb_url: str = Field(..., alias="MONGODB_URL")
    mongodb_database: str = Field(..., alias="MONGODB_DATABASE")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        gt=0,
    )
    frontend_origin: str = Field("http://localhost:5173", alias="FRONTEND_ORIGIN")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", alias="LOG_LEVEL"
    )
    enable_hsts: bool = Field(False, alias="ENABLE_HSTS")
    ai_demo_mode: bool = Field(False, alias="AI_DEMO_MODE")
    rate_limit_enabled: bool = Field(True, alias="RATE_LIMIT_ENABLED")
    rate_limit_window_seconds: int = Field(60, alias="RATE_LIMIT_WINDOW_SECONDS", ge=1, le=3600)
    rate_limit_registration: int = Field(5, alias="RATE_LIMIT_REGISTRATION", ge=1, le=1000)
    rate_limit_login: int = Field(10, alias="RATE_LIMIT_LOGIN", ge=1, le=1000)
    rate_limit_upload: int = Field(10, alias="RATE_LIMIT_UPLOAD", ge=1, le=1000)
    rate_limit_analysis: int = Field(30, alias="RATE_LIMIT_ANALYSIS", ge=1, le=5000)
    rate_limit_pdf_export: int = Field(10, alias="RATE_LIMIT_PDF_EXPORT", ge=1, le=1000)
    rate_limit_feedback: int = Field(20, alias="RATE_LIMIT_FEEDBACK", ge=1, le=1000)
    max_upload_size_mb: int = Field(5, alias="MAX_UPLOAD_SIZE_MB", gt=0, le=50)
    allowed_image_types: str = Field("image/jpeg,image/png", alias="ALLOWED_IMAGE_TYPES")
    upload_directory: Path = Field(Path("storage/temp_uploads"), alias="UPLOAD_DIRECTORY")
    temp_upload_expiry_minutes: int = Field(30, alias="TEMP_UPLOAD_EXPIRY_MINUTES", gt=0, le=1440)
    min_image_width: int = Field(
        300,
        validation_alias=AliasChoices("IMAGE_MIN_WIDTH", "MIN_IMAGE_WIDTH"),
        gt=0,
    )
    min_image_height: int = Field(
        300,
        validation_alias=AliasChoices("IMAGE_MIN_HEIGHT", "MIN_IMAGE_HEIGHT"),
        gt=0,
    )
    max_image_width: int = Field(
        6000,
        validation_alias=AliasChoices("IMAGE_MAX_WIDTH", "MAX_IMAGE_WIDTH"),
        gt=0,
    )
    max_image_height: int = Field(
        6000,
        validation_alias=AliasChoices("IMAGE_MAX_HEIGHT", "MAX_IMAGE_HEIGHT"),
        gt=0,
    )
    blur_fail_threshold: float = Field(60, alias="BLUR_FAIL_THRESHOLD", ge=0)
    blur_warning_threshold: float = Field(110, alias="BLUR_WARNING_THRESHOLD", ge=0)
    brightness_min_fail: float = Field(45, alias="BRIGHTNESS_MIN_FAIL", ge=0, le=255)
    brightness_min_warning: float = Field(75, alias="BRIGHTNESS_MIN_WARNING", ge=0, le=255)
    brightness_max_warning: float = Field(200, alias="BRIGHTNESS_MAX_WARNING", ge=0, le=255)
    brightness_max_fail: float = Field(225, alias="BRIGHTNESS_MAX_FAIL", ge=0, le=255)
    min_contrast_fail: float = Field(20, alias="MIN_CONTRAST_FAIL", ge=0, le=255)
    min_contrast_warning: float = Field(35, alias="MIN_CONTRAST_WARNING", ge=0, le=255)
    max_contrast_warning: float = Field(90, alias="MAX_CONTRAST_WARNING", ge=0, le=255)
    dark_pixel_threshold: int = Field(30, alias="DARK_PIXEL_THRESHOLD", ge=0, le=255)
    bright_pixel_threshold: int = Field(240, alias="BRIGHT_PIXEL_THRESHOLD", ge=0, le=255)
    max_dark_pixel_percent: float = Field(45, alias="MAX_DARK_PIXEL_PERCENT", ge=0, le=100)
    max_bright_pixel_percent: float = Field(35, alias="MAX_BRIGHT_PIXEL_PERCENT", ge=0, le=100)
    quality_pass_score: float = Field(70, alias="QUALITY_PASS_SCORE", ge=0, le=100)
    quality_warning_score: float = Field(50, alias="QUALITY_WARNING_SCORE", ge=0, le=100)
    min_suitable_aspect_ratio: float = Field(0.5, alias="MIN_SUITABLE_ASPECT_RATIO", gt=0)
    max_suitable_aspect_ratio: float = Field(2.0, alias="MAX_SUITABLE_ASPECT_RATIO", gt=0)
    face_crop_directory: Path = Field(Path("storage/temp_face_crops"), alias="FACE_CROP_DIRECTORY")
    face_detection_min_confidence: float = Field(
        0.60, alias="FACE_DETECTION_MIN_CONFIDENCE", gt=0, le=1
    )
    face_min_area_ratio: float = Field(0.15, alias="FACE_MIN_AREA_RATIO", gt=0, lt=1)
    face_max_area_ratio: float = Field(0.85, alias="FACE_MAX_AREA_RATIO", gt=0, le=1)
    face_max_center_offset: float = Field(0.25, alias="FACE_MAX_CENTER_OFFSET", gt=0, le=1)
    face_crop_padding_ratio: float = Field(0.18, alias="FACE_CROP_PADDING_RATIO", ge=0, le=1)
    face_min_crop_width: int = Field(224, alias="FACE_MIN_CROP_WIDTH", gt=0)
    face_min_crop_height: int = Field(224, alias="FACE_MIN_CROP_HEIGHT", gt=0)
    face_detection_max_faces: int = Field(1, alias="FACE_DETECTION_MAX_FACES", ge=1, le=5)
    face_crop_expiry_minutes: int = Field(30, alias="FACE_CROP_EXPIRY_MINUTES", gt=0, le=1440)
    face_edge_margin_ratio: float = Field(0.03, alias="FACE_EDGE_MARGIN_RATIO", ge=0, le=0.2)
    preprocessed_image_directory: Path = Field(
        Path("storage/temp_preprocessed_images"),
        alias="PREPROCESSED_IMAGE_DIRECTORY",
    )
    model_input_width: int = Field(224, alias="MODEL_INPUT_WIDTH", gt=0, le=2048)
    model_input_height: int = Field(224, alias="MODEL_INPUT_HEIGHT", gt=0, le=2048)
    model_input_channels: int = Field(3, alias="MODEL_INPUT_CHANNELS")
    model_input_colour_space: Literal["RGB"] = Field("RGB", alias="MODEL_INPUT_COLOUR_SPACE")
    preprocess_resize_mode: Literal["letterbox"] = Field(
        "letterbox", alias="PREPROCESS_RESIZE_MODE"
    )
    preprocess_padding_mode: Literal["reflect", "constant"] = Field(
        "reflect", alias="PREPROCESS_PADDING_MODE"
    )
    preprocess_normalization_mode: Literal["zero_to_one"] = Field(
        "zero_to_one", alias="PREPROCESS_NORMALIZATION_MODE"
    )
    preprocess_enable_denoise: bool = Field(True, alias="PREPROCESS_ENABLE_DENOISE")
    preprocess_denoise_strength: int = Field(3, alias="PREPROCESS_DENOISE_STRENGTH", ge=1, le=7)
    preprocess_noise_threshold: float = Field(4.0, alias="PREPROCESS_NOISE_THRESHOLD", ge=0, le=50)
    preprocess_enable_clahe: bool = Field(False, alias="PREPROCESS_ENABLE_CLAHE")
    preprocess_clahe_clip_limit: float = Field(1.5, alias="PREPROCESS_CLAHE_CLIP_LIMIT", gt=0, le=4)
    preprocess_clahe_grid_size: int = Field(8, alias="PREPROCESS_CLAHE_GRID_SIZE", ge=2, le=32)
    preprocess_enable_white_balance: bool = Field(False, alias="PREPROCESS_ENABLE_WHITE_BALANCE")
    preprocess_enable_sharpening: bool = Field(False, alias="PREPROCESS_ENABLE_SHARPENING")
    preprocess_alpha_background: int = Field(127, alias="PREPROCESS_ALPHA_BACKGROUND", ge=0, le=255)
    preprocess_upscale_warning_factor: float = Field(
        1.5, alias="PREPROCESS_UPSCALE_WARNING_FACTOR", gt=1, le=10
    )
    preprocessed_image_format: Literal["JPEG", "PNG"] = Field(
        "JPEG", alias="PREPROCESSED_IMAGE_FORMAT"
    )
    preprocessed_jpeg_quality: int = Field(95, alias="PREPROCESSED_JPEG_QUALITY", ge=80, le=100)
    preprocessed_image_expiry_minutes: int = Field(
        30, alias="PREPROCESSED_IMAGE_EXPIRY_MINUTES", gt=0, le=1440
    )
    skin_type_model_file: Path = Field(
        Path("app/ml/models/skin_type_model.keras"), alias="SKIN_TYPE_MODEL_PATH"
    )
    skin_type_metadata_file: Path = Field(
        Path("app/ml/models/skin_type_model_metadata.json"),
        alias="SKIN_TYPE_MODEL_METADATA_PATH",
    )
    skin_type_class_map_file: Path = Field(
        Path("app/ml/models/class_map.json"), alias="SKIN_TYPE_CLASS_MAP_PATH"
    )
    skin_type_min_confidence: float = Field(0.60, alias="SKIN_TYPE_MIN_CONFIDENCE", ge=0, le=1)
    skin_type_high_confidence: float = Field(0.80, alias="SKIN_TYPE_HIGH_CONFIDENCE", ge=0, le=1)
    skin_type_min_margin: float = Field(0.12, alias="SKIN_TYPE_MIN_MARGIN", ge=0, le=1)
    skin_concern_model_file: Path = Field(
        Path("app/ml/models/skin_concern_model.keras"),
        alias="SKIN_CONCERN_MODEL_PATH",
    )
    skin_concern_metadata_file: Path = Field(
        Path("app/ml/models/skin_concern_model_metadata.json"),
        alias="SKIN_CONCERN_MODEL_METADATA_PATH",
    )
    skin_concern_label_map_file: Path = Field(
        Path("app/ml/models/skin_concern_label_map.json"),
        alias="SKIN_CONCERN_LABEL_MAP_PATH",
    )
    skin_concern_thresholds_file: Path = Field(
        Path("app/ml/models/skin_concern_thresholds.json"),
        alias="SKIN_CONCERN_THRESHOLDS_PATH",
    )
    concern_uncertainty_margin: float = Field(
        0.05, alias="CONCERN_UNCERTAINTY_MARGIN", gt=0, le=0.25
    )
    concern_moderate_severity_distance: float = Field(
        0.25, alias="CONCERN_MODERATE_SEVERITY_DISTANCE", gt=0, lt=1
    )
    concern_prominent_severity_distance: float = Field(
        0.60, alias="CONCERN_PROMINENT_SEVERITY_DISTANCE", gt=0, lt=1
    )
    product_price_stale_days: int = Field(30, alias="PRODUCT_PRICE_STALE_DAYS", gt=0, le=3650)
    product_availability_stale_days: int = Field(
        14, alias="PRODUCT_AVAILABILITY_STALE_DAYS", gt=0, le=3650
    )
    product_source_verification_stale_days: int = Field(
        90, alias="PRODUCT_SOURCE_VERIFICATION_STALE_DAYS", gt=0, le=3650
    )
    budget_soft_overage_percent: float = Field(
        10, alias="BUDGET_SOFT_OVERAGE_PERCENT", ge=0, le=100
    )
    recommendation_weight_skin_type: float = Field(
        0.25, alias="RECOMMENDATION_WEIGHT_SKIN_TYPE", ge=0, le=1
    )
    recommendation_weight_concern: float = Field(
        0.25, alias="RECOMMENDATION_WEIGHT_CONCERN", ge=0, le=1
    )
    recommendation_weight_ingredient: float = Field(
        0.15, alias="RECOMMENDATION_WEIGHT_INGREDIENT", ge=0, le=1
    )
    recommendation_weight_sensitivity: float = Field(
        0.10, alias="RECOMMENDATION_WEIGHT_SENSITIVITY", ge=0, le=1
    )
    recommendation_weight_budget: float = Field(
        0.10, alias="RECOMMENDATION_WEIGHT_BUDGET", ge=0, le=1
    )
    recommendation_weight_availability: float = Field(
        0.05, alias="RECOMMENDATION_WEIGHT_AVAILABILITY", ge=0, le=1
    )
    recommendation_weight_brand: float = Field(
        0.04, alias="RECOMMENDATION_WEIGHT_BRAND", ge=0, le=1
    )
    recommendation_weight_data_quality: float = Field(
        0.03, alias="RECOMMENDATION_WEIGHT_DATA_QUALITY", ge=0, le=1
    )
    recommendation_weight_rating: float = Field(
        0.03, alias="RECOMMENDATION_WEIGHT_RATING", ge=0, le=1
    )
    penalty_eligible_with_caution: float = Field(
        5, alias="PENALTY_ELIGIBLE_WITH_CAUTION", ge=0, le=100
    )
    penalty_sensitivity_not_specified: float = Field(
        4, alias="PENALTY_SENSITIVITY_NOT_SPECIFIED", ge=0, le=100
    )
    penalty_active_ingredient_caution: float = Field(
        6, alias="PENALTY_ACTIVE_INGREDIENT_CAUTION", ge=0, le=100
    )
    penalty_fragrance_preference_conflict: float = Field(
        8, alias="PENALTY_FRAGRANCE_PREFERENCE_CONFLICT", ge=0, le=100
    )
    penalty_price_stale: float = Field(3, alias="PENALTY_PRICE_STALE", ge=0, le=100)
    penalty_availability_stale: float = Field(3, alias="PENALTY_AVAILABILITY_STALE", ge=0, le=100)
    penalty_limited_availability: float = Field(
        4, alias="PENALTY_LIMITED_AVAILABILITY", ge=0, le=100
    )
    penalty_significant_data_gap: float = Field(
        10, alias="PENALTY_SIGNIFICANT_DATA_GAP", ge=0, le=100
    )
    penalty_uncertain_skin_type: float = Field(3, alias="PENALTY_UNCERTAIN_SKIN_TYPE", ge=0, le=100)
    recommendation_max_total_penalty: float = Field(
        30, alias="RECOMMENDATION_MAX_TOTAL_PENALTY", ge=0, le=100
    )
    recommendation_min_display_score: float = Field(
        60, alias="RECOMMENDATION_MIN_DISPLAY_SCORE", ge=0, le=100
    )
    recommendation_max_per_category: int = Field(
        2, alias="RECOMMENDATION_MAX_PER_CATEGORY", ge=1, le=10
    )
    recommendation_max_same_brand: int = Field(
        2, alias="RECOMMENDATION_MAX_SAME_BRAND", ge=1, le=20
    )
    report_export_directory: Path = Field(
        Path("storage/temp_report_exports"), alias="REPORT_EXPORT_DIRECTORY"
    )
    report_export_expiry_minutes: int = Field(
        30, alias="REPORT_EXPORT_EXPIRY_MINUTES", gt=0, le=1440
    )
    report_pdf_include_profile_details: bool = Field(
        True, alias="REPORT_PDF_INCLUDE_PROFILE_DETAILS"
    )
    report_pdf_include_technical_details: bool = Field(
        False, alias="REPORT_PDF_INCLUDE_TECHNICAL_DETAILS"
    )
    feedback_max_submissions_per_hour: int = Field(
        20, alias="FEEDBACK_MAX_SUBMISSIONS_PER_HOUR", ge=1, le=200
    )
    feedback_duplicate_window_seconds: int = Field(
        60, alias="FEEDBACK_DUPLICATE_WINDOW_SECONDS", ge=0, le=3600
    )
    feedback_max_comment_length: int = Field(
        1000, alias="FEEDBACK_MAX_COMMENT_LENGTH", ge=100, le=5000
    )
    feedback_analytics_min_group_size: int = Field(
        3, alias="FEEDBACK_ANALYTICS_MIN_GROUP_SIZE", ge=1, le=100
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_image_quality_configuration(self) -> "Settings":
        origins = self.frontend_origin_list
        if not origins:
            raise ValueError("FRONTEND_ORIGIN must contain at least one origin.")
        for origin in origins:
            parsed = urlparse(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("FRONTEND_ORIGIN entries must be valid HTTP(S) origins.")
            if origin == "*" or parsed.path not in {"", "/"}:
                raise ValueError("FRONTEND_ORIGIN must not be a wildcard or contain a path.")
        if self.app_env.lower() in {"production", "staging"}:
            weak_secret = (
                len(self.jwt_secret_key) < 32
                or self.jwt_secret_key == "replace_with_a_secure_random_secret"
                or "change-me" in self.jwt_secret_key.lower()
            )
            if weak_secret:
                raise ValueError(
                    "JWT_SECRET_KEY must be a deployment-specific secret of at least 32 characters."
                )
        if self.min_image_width > self.max_image_width:
            raise ValueError("IMAGE_MIN_WIDTH cannot exceed IMAGE_MAX_WIDTH.")
        if self.min_image_height > self.max_image_height:
            raise ValueError("IMAGE_MIN_HEIGHT cannot exceed IMAGE_MAX_HEIGHT.")
        if self.blur_fail_threshold >= self.blur_warning_threshold:
            raise ValueError("BLUR_FAIL_THRESHOLD must be lower than BLUR_WARNING_THRESHOLD.")
        if not (
            self.brightness_min_fail
            < self.brightness_min_warning
            < self.brightness_max_warning
            < self.brightness_max_fail
        ):
            raise ValueError("Brightness thresholds must be strictly increasing.")
        if not (self.min_contrast_fail < self.min_contrast_warning < self.max_contrast_warning):
            raise ValueError("Contrast thresholds must be strictly increasing.")
        if self.dark_pixel_threshold >= self.bright_pixel_threshold:
            raise ValueError("DARK_PIXEL_THRESHOLD must be lower than BRIGHT_PIXEL_THRESHOLD.")
        if self.quality_warning_score >= self.quality_pass_score:
            raise ValueError("QUALITY_WARNING_SCORE must be lower than QUALITY_PASS_SCORE.")
        if self.min_suitable_aspect_ratio >= self.max_suitable_aspect_ratio:
            raise ValueError(
                "MIN_SUITABLE_ASPECT_RATIO must be lower than " "MAX_SUITABLE_ASPECT_RATIO."
            )
        if self.face_min_area_ratio >= self.face_max_area_ratio:
            raise ValueError("FACE_MIN_AREA_RATIO must be lower than FACE_MAX_AREA_RATIO.")
        if self.model_input_channels != 3:
            raise ValueError("MODEL_INPUT_CHANNELS must be 3 for the RGB contract.")
        if self.skin_type_min_confidence > self.skin_type_high_confidence:
            raise ValueError("SKIN_TYPE_MIN_CONFIDENCE cannot exceed SKIN_TYPE_HIGH_CONFIDENCE.")
        if self.concern_moderate_severity_distance >= self.concern_prominent_severity_distance:
            raise ValueError(
                "CONCERN_MODERATE_SEVERITY_DISTANCE must be lower than "
                "CONCERN_PROMINENT_SEVERITY_DISTANCE."
            )
        weights = (
            self.recommendation_weight_skin_type,
            self.recommendation_weight_concern,
            self.recommendation_weight_ingredient,
            self.recommendation_weight_sensitivity,
            self.recommendation_weight_budget,
            self.recommendation_weight_availability,
            self.recommendation_weight_brand,
            self.recommendation_weight_data_quality,
            self.recommendation_weight_rating,
        )
        if abs(sum(weights) - 1.0) > 1e-6:
            raise ValueError("Recommendation scoring weights must total 1.0.")
        return self

    @property
    def recommendation_weights(self) -> dict[str, float]:
        return {
            "skin_type_match": self.recommendation_weight_skin_type,
            "visible_concern_match": self.recommendation_weight_concern,
            "ingredient_relevance": self.recommendation_weight_ingredient,
            "sensitivity_compatibility": self.recommendation_weight_sensitivity,
            "budget_fit": self.recommendation_weight_budget,
            "availability": self.recommendation_weight_availability,
            "brand_preference": self.recommendation_weight_brand,
            "data_quality": self.recommendation_weight_data_quality,
            "rating": self.recommendation_weight_rating,
        }

    @property
    def is_testing(self) -> bool:
        return self.app_env.lower() == "testing"

    @property
    def is_deployed(self) -> bool:
        return self.app_env.lower() in {"production", "staging"}

    @property
    def frontend_origin_list(self) -> list[str]:
        return [
            value.strip().rstrip("/") for value in self.frontend_origin.split(",") if value.strip()
        ]

    @property
    def service_name(self) -> str:
        return f"{self.app_name} API"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_image_type_set(self) -> set[str]:
        return {
            value.strip().lower() for value in self.allowed_image_types.split(",") if value.strip()
        }

    @property
    def upload_path(self) -> Path:
        if self.upload_directory.is_absolute():
            return self.upload_directory.resolve()
        backend_root = Path(__file__).resolve().parents[2]
        return (backend_root / self.upload_directory).resolve()

    @property
    def face_crop_path(self) -> Path:
        if self.face_crop_directory.is_absolute():
            return self.face_crop_directory.resolve()
        backend_root = Path(__file__).resolve().parents[2]
        return (backend_root / self.face_crop_directory).resolve()

    @property
    def preprocessed_image_path(self) -> Path:
        if self.preprocessed_image_directory.is_absolute():
            return self.preprocessed_image_directory.resolve()
        backend_root = Path(__file__).resolve().parents[2]
        return (backend_root / self.preprocessed_image_directory).resolve()

    @property
    def report_export_path(self) -> Path:
        return self._backend_relative_path(self.report_export_directory)

    def _backend_relative_path(self, value: Path) -> Path:
        if value.is_absolute():
            return value.resolve()
        backend_root = Path(__file__).resolve().parents[2]
        return (backend_root / value).resolve()

    @property
    def skin_type_model_path(self) -> Path:
        return self._backend_relative_path(self.skin_type_model_file)

    @property
    def skin_type_metadata_path(self) -> Path:
        return self._backend_relative_path(self.skin_type_metadata_file)

    @property
    def skin_type_class_map_path(self) -> Path:
        return self._backend_relative_path(self.skin_type_class_map_file)

    @property
    def skin_concern_model_path(self) -> Path:
        return self._backend_relative_path(self.skin_concern_model_file)

    @property
    def skin_concern_metadata_path(self) -> Path:
        return self._backend_relative_path(self.skin_concern_metadata_file)

    @property
    def skin_concern_label_map_path(self) -> Path:
        return self._backend_relative_path(self.skin_concern_label_map_file)

    @property
    def skin_concern_thresholds_path(self) -> Path:
        return self._backend_relative_path(self.skin_concern_thresholds_file)


@lru_cache
def get_settings() -> Settings:
    return Settings()
