import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import get_settings

settings = get_settings()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".docx", ".zip"}


def _validate(file: UploadFile) -> None:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")


async def save_upload(file: UploadFile, subdir: str) -> str:
    _validate(file)

    target_dir = Path(settings.UPLOAD_DIR) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    size = 0
    chunk_size = 1024 * 1024
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    filename = f"{uuid.uuid4().hex}{Path(file.filename).suffix}"
    target = target_dir / filename

    with open(target, "wb") as out:
        while chunk := await file.read(chunk_size):
            size += len(chunk)
            if size > max_size:
                out.close()
                os.remove(target)
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds max size of {settings.MAX_UPLOAD_SIZE_MB}MB",
                )
            out.write(chunk)

    return f"/static/{subdir}/{filename}"
