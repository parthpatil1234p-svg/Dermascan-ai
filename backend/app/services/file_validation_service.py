import hashlib
import tempfile
import warnings
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.utils.file_utils import (
    UnsafeFilenameError,
    delete_file_safely,
    ensure_directory,
    secure_child_path,
    validated_image_extension,
)

CHUNK_SIZE_BYTES = 64 * 1024
FORMAT_BY_EXTENSION = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG"}
MIME_BY_FORMAT = {"JPEG": "image/jpeg", "PNG": "image/png"}
STORED_EXTENSION_BY_FORMAT = {"JPEG": ".jpg", "PNG": ".png"}


class UploadValidationError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedStoredImage:
    upload_id: str
    stored_filename: str
    storage_reference: str
    original_extension: str
    mime_type: str
    image_format: str
    file_size_bytes: int
    width: int
    height: int
    physical_path: Path


def _validate_and_sanitize_image(
    staging_path: Path,
    destination_path: Path,
    expected_format: str,
    declared_mime: str,
    settings: Settings,
) -> tuple[str, int, int]:
    previous_pixel_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = settings.max_image_width * settings.max_image_height

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(staging_path) as candidate:
                detected_format = candidate.format
                candidate.verify()

        if detected_format not in MIME_BY_FORMAT:
            raise UploadValidationError("The uploaded file is not a valid image.")
        if detected_format != expected_format:
            raise UploadValidationError("The uploaded file is not a valid image.")
        if MIME_BY_FORMAT[detected_format] != declared_mime:
            raise UploadValidationError("The uploaded file is not a valid image.")

        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(staging_path) as source:
                normalized = ImageOps.exif_transpose(source)
                normalized.load()
                width, height = normalized.size

                if width < settings.min_image_width or height < settings.min_image_height:
                    raise UploadValidationError(
                        "Image dimensions must be at least "
                        f"{settings.min_image_width} x {settings.min_image_height} pixels."
                    )
                if width > settings.max_image_width or height > settings.max_image_height:
                    raise UploadValidationError(
                        "Image dimensions must not exceed "
                        f"{settings.max_image_width} x {settings.max_image_height} pixels."
                    )

                sanitized = normalized.convert("RGB")
                if detected_format == "JPEG":
                    sanitized.save(
                        destination_path,
                        format="JPEG",
                        quality=92,
                        optimize=True,
                    )
                else:
                    sanitized.save(destination_path, format="PNG", optimize=True)

        with Image.open(destination_path) as sanitized_check:
            sanitized_check.verify()
        return detected_format, width, height
    except UploadValidationError:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
    ) as exc:
        raise UploadValidationError("The uploaded file is not a valid image.") from exc
    finally:
        Image.MAX_IMAGE_PIXELS = previous_pixel_limit


async def validate_and_store_image(
    uploaded_file: UploadFile,
    user_id: str,
    settings: Settings,
) -> ValidatedStoredImage:
    try:
        original_extension = validated_image_extension(uploaded_file.filename)
    except UnsafeFilenameError as exc:
        raise UploadValidationError("Only JPG, JPEG, and PNG images are supported.") from exc

    declared_mime = (uploaded_file.content_type or "").split(";", 1)[0].lower()
    expected_format = FORMAT_BY_EXTENSION[original_extension]
    if declared_mime not in settings.allowed_image_type_set:
        raise UploadValidationError("Only JPG, JPEG, and PNG images are supported.")
    if MIME_BY_FORMAT[expected_format] != declared_mime:
        raise UploadValidationError("The uploaded file is not a valid image.")

    storage_root = settings.upload_path
    ensure_directory(storage_root)
    user_folder_name = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:24]
    user_directory = secure_child_path(storage_root, user_folder_name)
    ensure_directory(user_directory)

    staging_handle = tempfile.NamedTemporaryFile(
        prefix=".upload-",
        suffix=".tmp",
        dir=user_directory,
        delete=False,
    )
    staging_path = Path(staging_handle.name)
    staging_handle.close()

    upload_id = str(uuid4())
    stored_extension = STORED_EXTENSION_BY_FORMAT[expected_format]
    stored_filename = f"{uuid4().hex}{stored_extension}"
    destination_path = secure_child_path(user_directory, stored_filename)

    try:
        total_bytes = 0
        with staging_path.open("wb") as staging_file:
            while chunk := await uploaded_file.read(CHUNK_SIZE_BYTES):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size_bytes:
                    raise UploadValidationError(
                        f"The selected image exceeds the {settings.max_upload_size_mb} MB upload limit.",
                        status.HTTP_413_CONTENT_TOO_LARGE,
                    )
                staging_file.write(chunk)

        if total_bytes == 0:
            raise UploadValidationError("The uploaded file is not a valid image.")

        image_format, width, height = await run_in_threadpool(
            _validate_and_sanitize_image,
            staging_path,
            destination_path,
            expected_format,
            declared_mime,
            settings,
        )
        sanitized_size = destination_path.stat().st_size
        if sanitized_size > settings.max_upload_size_bytes:
            raise UploadValidationError(
                f"The selected image exceeds the {settings.max_upload_size_mb} MB upload limit.",
                status.HTTP_413_CONTENT_TOO_LARGE,
            )

        storage_reference = destination_path.relative_to(storage_root).as_posix()
        return ValidatedStoredImage(
            upload_id=upload_id,
            stored_filename=stored_filename,
            storage_reference=storage_reference,
            original_extension=original_extension,
            mime_type=MIME_BY_FORMAT[image_format],
            image_format=image_format,
            file_size_bytes=sanitized_size,
            width=width,
            height=height,
            physical_path=destination_path,
        )
    except Exception:
        delete_file_safely(destination_path)
        raise
    finally:
        delete_file_safely(staging_path)
