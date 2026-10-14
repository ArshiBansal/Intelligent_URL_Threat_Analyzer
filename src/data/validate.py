"""
Record-level and batch-level validation for PhreshPhish data.

Ensures label integrity, required fields, and basic data quality
before storage or feature extraction.

Note: URL checks here are intentionally lenient for dataset rows.
User-facing input uses the stricter src/utils/validation.py.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from config.constants import LABEL_BENIGN, LABEL_PHISHING

logger = logging.getLogger(__name__)

_HEX = set("0123456789abcdef")


@dataclass
class DataQualityReport:
    """Container for validation statistics."""

    total: int = 0
    valid: int = 0
    invalid: int = 0
    missing_url: int = 0
    missing_label: int = 0
    invalid_label: int = 0
    missing_html: int = 0
    empty_html: int = 0
    malformed_url: int = 0
    duplicate_sha256: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "valid": self.valid,
            "invalid": self.invalid,
            "missing_url": self.missing_url,
            "missing_label": self.missing_label,
            "invalid_label": self.invalid_label,
            "missing_html": self.missing_html,
            "empty_html": self.empty_html,
            "malformed_url": self.malformed_url,
            "duplicate_sha256": self.duplicate_sha256,
            "error_count": len(self.errors),
            "sample_errors": self.errors[:20],
        }


def _is_valid_url(url: str) -> bool:
    """Lenient URL check for dataset rows."""
    if not url or not isinstance(url, str):
        return False
    url = url.strip()
    if len(url) < 4 or len(url) > 10000:
        return False
    try:
        test = url if "://" in url else "http://" + url
        parsed = urlparse(test)
        host = (parsed.netloc or "").strip()
        if not host or " " in host:
            return False
        return True
    except Exception:
        return False


def _is_valid_sha256(sha: Any) -> bool:
    if not sha or not isinstance(sha, str):
        return False
    s = sha.strip().lower()
    return len(s) == 64 and all(c in _HEX for c in s)


def validate_record(
    record: Dict[str, Any],
    require_html: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validate a single record.

    Returns
    -------
    (is_valid, list_of_error_messages)
    """
    errors: List[str] = []

    if not _is_valid_sha256(record.get("sha256")):
        errors.append("missing or invalid sha256")

    url = record.get("url")
    if not url:
        errors.append("missing url")
    elif not _is_valid_url(str(url)):
        errors.append("malformed url")

    label = record.get("label")
    if label is None:
        errors.append("missing label")
    elif label not in (LABEL_BENIGN, LABEL_PHISHING):
        errors.append(f"invalid label: {label!r}")

    html = record.get("html")
    if require_html:
        if html is None:
            errors.append("missing html")
        elif not str(html).strip():
            errors.append("empty html")

    date_val = record.get("date")
    if date_val is not None and not isinstance(date_val, (str, datetime)):
        errors.append("invalid date type")

    return len(errors) == 0, errors


def validate_batch(
    records: List[Dict[str, Any]],
    require_html: bool = False,
    check_duplicates: bool = True,
) -> DataQualityReport:
    """Validate a list of records and produce a quality report."""
    report = DataQualityReport()
    seen_sha: set[str] = set()

    for rec in records:
        report.total += 1
        is_valid, errs = validate_record(rec, require_html=require_html)

        if not is_valid:
            report.invalid += 1
            for e in errs:
                if "missing url" in e:
                    report.missing_url += 1
                elif "missing label" in e:
                    report.missing_label += 1
                elif "invalid label" in e:
                    report.invalid_label += 1
                elif "malformed url" in e:
                    report.malformed_url += 1
                elif "missing html" in e:
                    report.missing_html += 1
                elif "empty html" in e:
                    report.empty_html += 1
                report.errors.append(e)
            continue

        sha = (rec.get("sha256") or "").strip().lower()
        if check_duplicates and sha:
            if sha in seen_sha:
                report.duplicate_sha256 += 1
                report.invalid += 1
                report.errors.append(f"duplicate sha256: {sha}")
                continue
            seen_sha.add(sha)

        report.valid += 1

    return report