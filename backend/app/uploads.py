"""Document upload handling: validate, store, and re-index user documents."""
import os
import re
import logging

from app.config import DATA_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = MAX_UPLOAD_SIZE
MAX_FILES_PER_REQUEST = 10

_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._\-]")


def sanitize_filename(name: str) -> str:
    """Strip path components and unsafe characters from an uploaded filename."""
    name = os.path.basename(name.replace("\\", "/")).strip()
    name = _SAFE_NAME.sub("_", name)
    if not name:
        raise ValueError("Empty filename")
    return name


def unique_path(dir_path: str, name: str) -> str:
    """Return a path that does not collide with existing files."""
    base, ext = os.path.splitext(name)
    candidate = os.path.join(dir_path, name)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(dir_path, f"{base}_{counter}{ext}")
        counter += 1
    return candidate


def store_upload(filename: str, content: bytes) -> str:
    """Validate and persist a single uploaded file into the corpus directory."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")
    if len(content) == 0:
        raise ValueError("File is empty")
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File exceeds the {MAX_FILE_SIZE // (1024 * 1024)} MB size limit")

    safe_name = sanitize_filename(filename)
    path = unique_path(DATA_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(content)
    logger.info(f"Stored uploaded document: {os.path.basename(path)}")
    return os.path.basename(path)
