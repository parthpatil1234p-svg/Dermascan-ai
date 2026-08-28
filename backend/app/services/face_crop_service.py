import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np

from app.core.config import Settings
from app.utils.bounding_box import PixelBoundingBox
from app.utils.file_utils import (
    delete_file_safely,
    delete_storage_reference,
    ensure_directory,
    secure_child_path,
)

logger = logging.getLogger(__name__)


class FaceCropTooSmallError(Exception):
    pass


class FaceCropStorageError(Exception):
    pass


@dataclass(frozen=True)
class StoredFaceCrop:
    storage_reference: str
    crop_format: str
    crop_width: int
    crop_height: int
    crop_file_size: int
    physical_path: Path


def create_private_face_crop(
    *,
    image: np.ndarray,
    crop_box: PixelBoundingBox,
    user_id: str,
    upload_id: str,
    settings: Settings,
) -> StoredFaceCrop:
    crop = image[
        crop_box.y : crop_box.y + crop_box.height,
        crop_box.x : crop_box.x + crop_box.width,
    ]
    if crop.size == 0:
        raise FaceCropStorageError

    crop_height, crop_width = crop.shape[:2]
    if crop_width < settings.face_min_crop_width or crop_height < settings.face_min_crop_height:
        raise FaceCropTooSmallError

    crop_root = settings.face_crop_path
    ensure_directory(crop_root)
    user_folder = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:24]
    upload_folder = hashlib.sha256(upload_id.encode("utf-8")).hexdigest()[:24]
    crop_directory = secure_child_path(crop_root, user_folder, upload_folder)
    ensure_directory(crop_directory)

    crop_filename = f"{uuid4().hex}.jpg"
    crop_path = secure_child_path(crop_directory, crop_filename)

    try:
        saved = cv2.imwrite(
            str(crop_path),
            crop,
            [int(cv2.IMWRITE_JPEG_QUALITY), 92],
        )
    except Exception as exc:
        raise FaceCropStorageError from exc

    if not saved or not crop_path.is_file():
        delete_file_safely(crop_path)
        raise FaceCropStorageError

    return StoredFaceCrop(
        storage_reference=crop_path.relative_to(crop_root).as_posix(),
        crop_format="JPEG",
        crop_width=crop_width,
        crop_height=crop_height,
        crop_file_size=crop_path.stat().st_size,
        physical_path=crop_path,
    )


def delete_face_crop_reference(settings: Settings, storage_reference: str | None) -> bool:
    if not storage_reference:
        return False
    return delete_storage_reference(settings.face_crop_path, storage_reference)


async def cleanup_expired_face_crops(collection, settings: Settings) -> int:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    cursor = collection.find({"expires_at": {"$lte": now}})
    cleaned_count = 0
    async for document in cursor:
        delete_face_crop_reference(settings, document.get("crop_reference"))
        await collection.delete_one({"_id": document["_id"]})
        cleaned_count += 1
        logger.info("Expired face crop cleaned.")
    return cleaned_count
