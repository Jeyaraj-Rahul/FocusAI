from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


async def save_upload(file: UploadFile, subdirectory: str, allowed_suffixes: set[str]) -> Path:
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed_suffixes:
        allowed = ", ".join(sorted(allowed_suffixes))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file type. Allowed: {allowed}")

    target_dir = Path(settings.STORAGE_DIR) / "uploads" / subdirectory
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{uuid4().hex}{suffix}"
    content = await file.read()
    target_path.write_bytes(content)
    return target_path
