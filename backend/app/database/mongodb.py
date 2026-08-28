from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from app.core.config import Settings


class MongoConnection:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient | None = None
        self.database: AsyncIOMotorDatabase | None = None

    async def connect(self, settings: Settings) -> AsyncIOMotorDatabase:
        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,
                tz_aware=True,
            )
            await self.client.admin.command("ping")
            self.database = self.client[settings.mongodb_database]
            await self.ensure_indexes()
            return self.database
        except ServerSelectionTimeoutError as exc:
            raise RuntimeError(
                "Could not connect to MongoDB. Check MONGODB_URL and ensure MongoDB is running."
            ) from exc
        except PyMongoError as exc:
            raise RuntimeError("MongoDB initialization failed.") from exc

    async def ensure_indexes(self) -> None:
        if self.database is None:
            raise RuntimeError("MongoDB database is not initialized.")

        await self.database["users"].create_index("email", unique=True)
        await self.database["skin_profiles"].create_index("user_id", unique=True)
        await self.database["image_uploads"].create_index("upload_id", unique=True)
        await self.database["image_uploads"].create_index("user_id")
        await self.database["image_uploads"].create_index("expires_at")
        await self.database["image_quality_reports"].create_index("quality_report_id", unique=True)
        await self.database["image_quality_reports"].create_index("upload_id", unique=True)
        await self.database["image_quality_reports"].create_index("user_id")
        await self.database["face_detection_reports"].create_index("face_report_id", unique=True)
        await self.database["face_detection_reports"].create_index("upload_id", unique=True)
        await self.database["face_detection_reports"].create_index("user_id")
        await self.database["face_detection_reports"].create_index("expires_at")
        await self.database["image_preprocessing_reports"].create_index(
            "preprocessing_report_id", unique=True
        )
        await self.database["image_preprocessing_reports"].create_index("upload_id", unique=True)
        await self.database["image_preprocessing_reports"].create_index("user_id")
        await self.database["image_preprocessing_reports"].create_index("expires_at")
        await self.database["skin_type_reports"].create_index("skin_type_report_id", unique=True)
        await self.database["skin_type_reports"].create_index("upload_id", unique=True)
        await self.database["skin_type_reports"].create_index("user_id")
        await self.database["skin_concern_reports"].create_index(
            "skin_concern_report_id", unique=True
        )
        await self.database["skin_concern_reports"].create_index("upload_id", unique=True)
        await self.database["skin_concern_reports"].create_index("user_id")
        await self.database["products"].create_index("product_id", unique=True)
        await self.database["products"].create_index("slug", unique=True)
        await self.database["products"].create_index("brand_id")
        await self.database["products"].create_index("category")
        await self.database["products"].create_index("suitable_skin_types")
        await self.database["products"].create_index("target_visible_concerns")
        await self.database["products"].create_index("normalized_ingredients")
        await self.database["products"].create_index("country_codes")
        await self.database["products"].create_index("availability_status")
        await self.database["products"].create_index("is_active")
        await self.database["products"].create_index("data_type")
        await self.database["products"].create_index("price.amount")
        await self.database["products"].create_index(
            [
                ("product_name", "text"),
                ("brand_name", "text"),
                ("short_description", "text"),
                ("highlighted_ingredients", "text"),
            ],
            name="product_catalogue_text",
        )
        await self.database["ingredients"].create_index("ingredient_id", unique=True)
        await self.database["ingredients"].create_index("normalized_name", unique=True)
        await self.database["ingredients"].create_index("normalized_aliases")
        await self.database["ingredients"].create_index("ingredient_category")
        await self.database["brands"].create_index("brand_id", unique=True)
        await self.database["brands"].create_index("normalized_name", unique=True)
        await self.database["product_import_jobs"].create_index("import_job_id", unique=True)
        await self.database["product_import_jobs"].create_index("created_at")
        await self.database["product_eligibility_reports"].create_index(
            "eligibility_report_id", unique=True
        )
        await self.database["product_eligibility_reports"].create_index("upload_id", unique=True)
        await self.database["product_eligibility_reports"].create_index("user_id")
        await self.database["product_recommendation_reports"].create_index(
            "recommendation_report_id", unique=True
        )
        await self.database["product_recommendation_reports"].create_index("upload_id", unique=True)
        await self.database["product_recommendation_reports"].create_index("user_id")
        await self.database["skincare_routine_reports"].create_index(
            "routine_report_id", unique=True
        )
        await self.database["skincare_routine_reports"].create_index("upload_id", unique=True)
        await self.database["skincare_routine_reports"].create_index("user_id")
        await self.database["final_skin_reports"].create_index("final_report_id", unique=True)
        await self.database["final_skin_reports"].create_index(
            [("upload_id", 1), ("report_version", 1)], unique=True
        )
        await self.database["final_skin_reports"].create_index(
            [("user_id", 1), ("generated_at", -1)]
        )
        await self.database["final_skin_reports"].create_index("report_status")
        await self.database["final_skin_reports"].create_index("is_archived")
        await self.database["user_feedback"].create_index("feedback_id", unique=True)
        await self.database["user_feedback"].create_index([("user_id", 1), ("created_at", -1)])
        await self.database["user_feedback"].create_index("final_report_id")
        await self.database["user_feedback"].create_index("product_id")
        await self.database["user_feedback"].create_index("payload_hash")
        await self.database["user_product_avoidance"].create_index(
            [("user_id", 1), ("product_id", 1)], unique=True
        )
        await self.database["recommendation_improvement_signals"].create_index(
            [("source_feedback_id", 1), ("signal_type", 1)], unique=True
        )
        await self.database["recommendation_improvement_signals"].create_index("user_id")
        await self.database["catalogue_review_signals"].create_index("signal_id", unique=True)
        await self.database["catalogue_review_signals"].create_index(
            [("product_id", 1), ("signal_type", 1)], unique=True
        )
        await self.database["feedback_analytics_snapshots"].create_index("snapshot_id", unique=True)
        await self.database["feedback_analytics_snapshots"].create_index("created_at")
        await self.database["feedback_moderation_audit"].create_index("feedback_id")

    async def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
            self.database = None


mongo_connection = MongoConnection()
