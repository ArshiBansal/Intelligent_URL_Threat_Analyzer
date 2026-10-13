"""
Miscellaneous helpers: logging setup, timing decorator,
hashing, truncation, JSON safety and chunking.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from datetime import datetime, date
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Generator, Iterable, List, Optional, TypeVar

from config.settings import settings

T = TypeVar("T")

def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> None:
    """
    Configure root logger for both scripts and the Streamlit app.
    """
    level = (level or settings.LOG_LEVEL).upper()
    numeric = getattr(logging, level, logging.INFO)

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=numeric,
        format=fmt,
        datefmt=datefmt,
        handlers=handlers,
        force=True,  # override any previous config
    )

def timed(func: Callable[..., T]) -> Callable[..., T]:
    """Simple decorator that logs execution time."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logging.getLogger(func.__module__).debug(
            "%s took %.3f s", func.__qualname__, elapsed
        )
        return result

    return wrapper

def sha256_hex(data: str | bytes) -> str:
    """Return the hex digest of SHA-256."""
    if isinstance(data, str):
        data = data.encode("utf-8", errors="replace")
    return hashlib.sha256(data).hexdigest()

def truncate(text: str, max_len: int = 200, suffix: str = "…") -> str:
    """Truncate a string for safe display in tables / logs."""
    if not text or len(text) <= max_len:
        return text or ""
    return text[: max_len - len(suffix)] + suffix

def _default_serializer(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "tolist"):  # numpy arrays
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def safe_json_serialize(obj: Any, **kwargs) -> str:
    """json.dumps with sensible defaults for common non-serializable types."""
    return json.dumps(obj, default=_default_serializer, **kwargs)

def chunked(iterable: Iterable[T], size: int) -> Generator[List[T], None, None]:
    """
    Yield successive chunks of length `size` from an iterable.
    Useful for batch MongoDB writes and streaming processing.
    """
    if size < 1:
        raise ValueError("chunk size must be >= 1")
    chunk: List[T] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk