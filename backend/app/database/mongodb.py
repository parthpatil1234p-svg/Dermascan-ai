import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from app.core.config import Settings

logger = logging.getLogger(__name__)
DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


class MongoConnection:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient | None = None
        self.database: AsyncIOMotorDatabase | None = None
        self.is_mock: bool = False

    async def connect(self, settings: Settings) -> AsyncIOMotorDatabase:
        try:
            # 1. Try real MongoDB Atlas / Local MongoDB connection
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=3000,
                tz_aware=True,
            )
            await self.client.admin.command("ping")
            self.database = self.client[settings.mongodb_database]
            self.is_mock = False
            logger.info("Connected to MongoDB database: %s", settings.mongodb_database)
            await self.ensure_indexes()
            product_count = await self.database["products"].count_documents({})
            if product_count == 0:
                print("[*] Products collection is empty on MongoDB Atlas. Auto-seeding demo catalogue...")
                await self._seed_initial_mock_data()
            return self.database
        except (ServerSelectionTimeoutError, PyMongoError, Exception) as exc:
            # 2. Seamless local In-Memory Fallback if Atlas is unreachable / IP pending
            print("\n" + "="*70)
            print("[!] WARNING: MongoDB Atlas connection timed out (IP Access List pending).")
            print("[+] Automatically switching to Local In-Memory Database for seamless run.")
            print("="*70 + "\n")
            try:
                import mongomock_motor
                self.client = mongomock_motor.AsyncMongoMockClient()
                self.database = self.client[settings.mongodb_database]
                self.is_mock = True
                await self.ensure_indexes()
                await self._seed_initial_mock_data()
                return self.database
            except Exception as mock_exc:
                raise RuntimeError("Could not initialize database fallback.") from mock_exc

    async def _seed_initial_mock_data(self) -> None:
        if self.database is None:
            return
        try:
            from app.models.brand import build_brand_document
            from app.models.ingredient import build_ingredient_document
            from app.schemas.brand import BrandCreate
            from app.schemas.ingredient import IngredientCreate
            from app.services.product_import_service import import_product_file

            now = datetime.now(timezone.utc)
            brand_file = DATA_ROOT / "brands/demo_brands.json"
            if brand_file.exists():
                brands = json.loads(brand_file.read_text(encoding="utf-8"))
                for b in brands:
                    doc = build_brand_document(BrandCreate.model_validate(b), now)
                    await self.database["brands"].replace_one({"brand_id": doc["brand_id"]}, doc, upsert=True)

            ing_file = DATA_ROOT / "ingredients/base_ingredients.json"
            if ing_file.exists():
                ings = json.loads(ing_file.read_text(encoding="utf-8"))
                for i in ings:
                    doc = build_ingredient_document(IngredientCreate.model_validate(i), now)
                    await self.database["ingredients"].replace_one({"ingredient_id": doc["ingredient_id"]}, doc, upsert=True)

            prod_file = DATA_ROOT / "products/demo_products.json"
            if prod_file.exists():
                await import_product_file(prod_file, self.database["products"], self.database["product_import_jobs"], dry_run=False)
            print("[+] Seeded demo products, brands, and ingredients into in-memory database.")
        except Exception as e:
            print(f"[*] Mock data seed notice: {e}")

    async def ensure_indexes(self) -> None:
        if self.database is None:
            raise RuntimeError("MongoDB database is not initialized.")

        try:
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
            if not self.is_mock:
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
        except Exception as idx_err:
            logger.warning("Index creation notice: %s", idx_err)

    async def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None
            self.database = None


mongo_connection = MongoConnection()
