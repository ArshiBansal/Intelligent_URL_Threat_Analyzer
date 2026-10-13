"""
Data package: ingestion, validation, and exploration of the PhreshPhish dataset.
Dataset is always loaded via the Hugging Face `datasets` library (never CSV download).
"""

from .ingest import ingest_phreshphish
from .validate import validate_record, validate_batch, DataQualityReport
from .explore import generate_data_quality_report, class_distribution

__all__ = [
    "ingest_phreshphish",
    "validate_record",
    "validate_batch",
    "DataQualityReport",
    "generate_data_quality_report",
    "class_distribution",
]