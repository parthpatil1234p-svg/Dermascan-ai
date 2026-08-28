from pathlib import Path

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


class UnsafeFilenameError(ValueError):
    pass


def validated_image_extension(filename: str | None) -> str:
    if not filename or "\x00" in filename:
        raise UnsafeFilenameError
    if "/" in filename or "\\" in filename or filename in {".", ".."}:
        raise UnsafeFilenameError

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise UnsafeFilenameError
    return extension


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def secure_child_path(root: Path, *parts: str) -> Path:
    resolved_root = root.resolve()
    candidate = resolved_root.joinpath(*parts).resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise ValueError("Unsafe storage reference.")
    return candidate


def delete_file_safely(path: Path) -> bool:
    try:
        path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def delete_storage_reference(root: Path, storage_reference: str) -> bool:
    try:
        target = secure_child_path(root, *Path(storage_reference).parts)
    except ValueError:
        return False
    return delete_file_safely(target)
