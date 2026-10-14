#!/usr/bin/env python3
"""
Phase 8 – Export / verify artifacts and optionally promote latest_*.

Usage:
    python scripts/08_export_artifacts.py --promote
    python scripts/08_export_artifacts.py --selected random_forest --promote
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from config.constants import CURRENT_MODEL_VERSION, SUPPORTED_MODEL_NAMES
from src.utils.helpers import setup_logging, safe_json_serialize
from scripts.ml_feature_utils import FEATURE_NAMES

logger = logging.getLogger("export_artifacts")


def find_artifacts(model_name: str) -> Dict[str, Optional[Path]]:
    models_dir = settings.MODELS_DIR
    meta_dir = settings.METADATA_DIR
    prep_dir = settings.PREPROCESSORS_DIR

    def newest(directory: Path, pattern: str) -> Optional[Path]:
        files = sorted(
            directory.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return files[0] if files else None

    return {
        "model": newest(models_dir, f"{model_name}_*.joblib"),
        "metadata": newest(meta_dir, f"{model_name}_*.json"),
        "eval": newest(meta_dir, f"eval_{model_name}_*.json"),
        "preprocessor": newest(prep_dir, f"preprocessor_{model_name}_*.joblib"),
    }


def build_manifest(selected: Optional[str] = None) -> Dict[str, Any]:
    entries = []
    for name in SUPPORTED_MODEL_NAMES:
        paths = find_artifacts(name)
        entry = {
            "model_name": name,
            "model_path": str(paths["model"]) if paths["model"] else None,
            "metadata_path": str(paths["metadata"]) if paths["metadata"] else None,
            "eval_path": str(paths["eval"]) if paths["eval"] else None,
            "preprocessor_path": str(paths["preprocessor"]) if paths["preprocessor"] else None,
            "exists": paths["model"] is not None,
        }
        if paths["model"]:
            entry["size_bytes"] = paths["model"].stat().st_size
            entry["modified"] = datetime.fromtimestamp(
                paths["model"].stat().st_mtime, tz=timezone.utc
            ).isoformat()
        entries.append(entry)

    if selected is None:
        sel_path = settings.REPORTS_DIR / "model_selection.json"
        if sel_path.exists():
            with open(sel_path, encoding="utf-8") as f:
                selected = json.load(f).get("selected_model")
    if selected is None:
        for e in entries:
            if e["exists"]:
                selected = e["model_name"]
                break

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": CURRENT_MODEL_VERSION,
        "selected_model": selected,
        "feature_names": list(FEATURE_NAMES),
        "feature_dim": len(FEATURE_NAMES),
        "models": entries,
        "artifacts_dir": str(settings.ARTIFACTS_DIR),
    }


def promote_latest(model_name: str) -> None:
    paths = find_artifacts(model_name)
    if not paths["model"]:
        logger.warning("No model file for %s – cannot promote", model_name)
        return

    settings.ensure_directories()
    latest_model = settings.MODELS_DIR / "latest_model.joblib"
    shutil.copy2(paths["model"], latest_model)
    logger.info("Promoted model → %s", latest_model)

    # Prefer training metadata (has feature_names); fall back to eval JSON
    meta_src = paths["metadata"] or paths["eval"]
    if meta_src:
        latest_meta = settings.METADATA_DIR / "latest_metadata.json"
        shutil.copy2(meta_src, latest_meta)
        logger.info("Promoted metadata → %s", latest_meta)

        # Ensure feature_names present in promoted metadata
        try:
            with open(latest_meta, encoding="utf-8") as f:
                meta = json.load(f)
            if "feature_names" not in meta:
                meta["feature_names"] = list(FEATURE_NAMES)
                meta["feature_dim"] = len(FEATURE_NAMES)
                with open(latest_meta, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
                logger.info("Injected feature_names into latest_metadata.json")
        except Exception as exc:
            logger.warning("Could not patch metadata feature_names: %s", exc)

    if paths["preprocessor"]:
        latest_prep = settings.PREPROCESSORS_DIR / "latest_preprocessor.joblib"
        shutil.copy2(paths["preprocessor"], latest_prep)
        logger.info("Promoted preprocessor → %s", latest_prep)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export / verify model artifacts")
    parser.add_argument("--selected", default=None)
    parser.add_argument("--promote", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=settings.ARTIFACTS_DIR / "manifest.json",
    )
    args = parser.parse_args()

    setup_logging()
    settings.ensure_directories()

    manifest = build_manifest(selected=args.selected)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(safe_json_serialize(manifest, indent=2))
    logger.info("Manifest → %s", args.output)

    for e in manifest["models"]:
        logger.info("  %-20s %s", e["model_name"], "OK" if e["exists"] else "MISSING")

    selected = manifest.get("selected_model")
    logger.info("Selected model: %s", selected)

    if args.promote and selected:
        promote_latest(selected)
    elif args.promote and not selected:
        logger.warning("--promote set but no selected model found")

    missing = [e["model_name"] for e in manifest["models"] if not e["exists"]]
    if missing:
        logger.warning("Missing artifacts for: %s (run script 06 first)", missing)
    else:
        logger.info("All expected model artifacts are present.")


if __name__ == "__main__":
    main()