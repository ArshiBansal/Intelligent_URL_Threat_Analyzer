"""
Phase 1 – Schema & label audit for PhreshPhish.

- Loads a small streaming sample via the Hugging Face datasets library
- Verifies field presence, label values, missingness and basic types
- Writes a human-readable report to data/reports/
- Does NOT write to MongoDB

Usage:
    python scripts/01_schema_audit.py
    python scripts/01_schema_audit.py --max-samples 2000 --split train
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from datasets import load_dataset

from config.settings import settings
from config.constants import (
    DATASET_HF_ID,
    DATASET_DISPLAY_NAME,
    LABEL_BENIGN,
    LABEL_PHISHING,
    SOURCE_FIELDS,
)
from src.utils.helpers import setup_logging, safe_json_serialize

logger = logging.getLogger("schema_audit")


def audit_sample(
    split: str = "train",
    max_samples: int = 2000,
) -> Dict[str, Any]:
    """Stream a sample and collect schema / quality statistics."""
    logger.info(
        "Loading %s (split=%s, max_samples=%d) in streaming mode…",
        DATASET_HF_ID,
        split,
        max_samples,
    )

    ds = load_dataset(
        DATASET_HF_ID,
        split=split,
        streaming=True,
        token=settings.HF_TOKEN,
    )

    field_presence: Counter = Counter()
    field_types: Dict[str, Counter] = defaultdict(Counter)
    label_counts: Counter = Counter()
    missing_html = 0
    empty_html = 0
    malformed_url = 0
    total = 0
    example_records: List[Dict[str, Any]] = []

    for i, rec in enumerate(ds):
        if i >= max_samples:
            break
        total += 1

        for field in SOURCE_FIELDS:
            val = rec.get(field)
            if val is not None and val != "":
                field_presence[field] += 1
                field_types[field][type(val).__name__] += 1
            else:
                if field == "html":
                    missing_html += 1

        label = rec.get("label")
        label_counts[label] += 1

        html = rec.get("html")
        if html is not None and not str(html).strip():
            empty_html += 1

        url = rec.get("url")
        if not url or not isinstance(url, str) or len(url) < 8:
            malformed_url += 1

        if i < 3:  # keep a few raw examples (HTML truncated)
            sample = {k: rec.get(k) for k in SOURCE_FIELDS}
            if sample.get("html"):
                sample["html"] = str(sample["html"])[:500] + "…"
            example_records.append(sample)

    report = {
        "dataset": DATASET_DISPLAY_NAME,
        "hf_id": DATASET_HF_ID,
        "split": split,
        "samples_audited": total,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "field_presence": dict(field_presence),
        "field_presence_pct": {
            k: round(v / total * 100, 2) if total else 0.0
            for k, v in field_presence.items()
        },
        "field_types": {k: dict(v) for k, v in field_types.items()},
        "label_counts": dict(label_counts),
        "label_values_expected": [LABEL_BENIGN, LABEL_PHISHING],
        "unexpected_labels": [
            lab for lab in label_counts if lab not in (LABEL_BENIGN, LABEL_PHISHING)
        ],
        "missing_html": missing_html,
        "empty_html": empty_html,
        "malformed_url_approx": malformed_url,
        "example_records": example_records,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="PhreshPhish schema audit")
    parser.add_argument("--split", default="train", choices=["train", "test"])
    parser.add_argument("--max-samples", type=int, default=2000)
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.REPORTS_DIR / "schema_audit.json",
    )
    args = parser.parse_args()

    setup_logging()
    settings.ensure_directories()

    report = audit_sample(split=args.split, max_samples=args.max_samples)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(safe_json_serialize(report, indent=2))

    logger.info("Audit complete → %s", args.output)
    logger.info("Label distribution: %s", report["label_counts"])
    if report["unexpected_labels"]:
        logger.warning("Unexpected label values found: %s", report["unexpected_labels"])
    else:
        logger.info("All labels match expected values (%s / %s)", LABEL_BENIGN, LABEL_PHISHING)


if __name__ == "__main__":
    main()