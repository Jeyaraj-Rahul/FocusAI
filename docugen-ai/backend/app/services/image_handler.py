from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/bmp", "image/gif"}
MAX_IMAGE_WIDTH = 1400
MAX_IMAGE_HEIGHT = 1000


async def process_screenshot_upload(file: UploadFile) -> dict:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload must be a PNG, JPG, BMP, or GIF image")

    content = await file.read()
    try:
        image = Image.open(BytesIO(content))
        image = ImageOps.exif_transpose(image)
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file") from exc

    original_width, original_height = image.size
    image.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)
    resized_width, resized_height = image.size

    output_dir = Path(settings.STORAGE_DIR) / "uploads" / "screenshots"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{uuid4().hex}.png"

    if image.mode not in {"RGB", "RGBA"}:
        image = image.convert("RGBA")
    image.save(output_path, format="PNG", optimize=True)

    return {
        "path": output_path,
        "width_px": resized_width,
        "height_px": resized_height,
        "original_width_px": original_width,
        "original_height_px": original_height,
        "alignment": "center",
        "width_inches": _recommended_width_inches(resized_width, resized_height),
    }


def _recommended_width_inches(width: int, height: int) -> float:
    if height > width:
        return 4.0
    if width / max(height, 1) > 1.8:
        return 6.2
    return 5.8
