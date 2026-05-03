import os
import uuid
from pathlib import Path
from fastapi import HTTPException
from app.core.config import get_settings

settings = get_settings()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_image(content_type: str, file_size: int) -> None:
    """
    Check that uploaded file is a valid image within size limit.
    Raises HTTPException if invalid — FastAPI handles this automatically.
    """
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {content_type}. "
                   f"Allowed: JPEG, PNG, WebP"
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: "
                   f"{settings.max_upload_size_mb}MB"
        )


def save_upload(image_bytes: bytes, content_type: str) -> str:
    """
    Save uploaded image to the uploads directory.
    Returns the relative file path.
    
    Uses UUID for filename to prevent:
    - Duplicate filename collisions
    - Path traversal attacks (malicious filenames)
    """
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Map MIME type to extension
    ext_map = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp"
    }
    ext = ext_map.get(content_type, ".jpg")
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = upload_dir / filename

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    return str(file_path)