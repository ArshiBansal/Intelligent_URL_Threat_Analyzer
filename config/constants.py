"""
Project-wide constants that never change at runtime.
These values are part of the specification and must stay consistent.
"""

from __future__ import annotations

DATASET_DISPLAY_NAME = "PhreshPhish"
DATASET_HF_ID = "phreshphish/phreshphish"
DATASET_LICENSE = "CC-BY-4.0"
DATASET_PAPER = "https://arxiv.org/abs/2507.10854"
DATASET_HF_URL = "https://huggingface.co/datasets/phreshphish/phreshphish"

# Official label values in PhreshPhish
LABEL_BENIGN = "benign"
LABEL_PHISHING = "phish"          # dataset uses "phish" (not "phishing")
LABEL_MAP = {
    "benign": 0,
    "phish": 1,
}
LABEL_INVERSE_MAP = {v: k for k, v in LABEL_MAP.items()}

# Human-readable display names
LABEL_DISPLAY = {
    "benign": "Benign",
    "phish": "Phishing",
}

SOURCE_FIELDS = [
    "sha256",
    "url",
    "label",
    "target",
    "date",
    "lang",
    "lang_score",
    "html",
]

URL_FEATURE_NAMES = [
    "url_length",
    "hostname_length",
    "path_length",
    "query_length",
    "num_dots",
    "num_hyphens",
    "num_underscores",
    "num_slashes",
    "num_question_marks",
    "num_equals",
    "num_at",
    "num_ampersand",
    "num_exclamation",
    "num_tilde",
    "num_comma",
    "num_plus",
    "num_asterisk",
    "num_hash",
    "num_dollar",
    "num_percent",
    "has_ip_address",
    "has_https",
    "has_www",
    "is_shortened",
    "num_subdomains",
    "tld_length",
    "has_suspicious_tld",
    "has_login_keyword",
    "has_secure_keyword",
    "has_account_keyword",
    "has_update_keyword",
    "has_verify_keyword",
    "has_bank_keyword",
    "has_paypal_keyword",
]

HTML_FEATURE_NAMES = [
    "html_length",
    "num_forms",
    "num_inputs",
    "num_password_inputs",
    "num_hidden_inputs",
    "num_links",
    "num_external_links",
    "num_internal_links",
    "num_images",
    "num_scripts",
    "num_iframes",
    "has_title",
    "title_length",
    "has_meta_description",
    "num_meta_tags",
    "has_favicon",
    "num_buttons",
    "has_login_form",
    "has_suspicious_js",
]

CURRENT_MODEL_VERSION = "v1.0.0"
SUPPORTED_MODEL_NAMES = [
    "logistic_regression",
    "random_forest",
    "xgboost",
    "gradient_boosting",
]

# Default decision threshold (can be overridden by saved metadata)
DEFAULT_THRESHOLD = 0.5

# UI risk bands on P(phish) — used by predict.py
RISK_BAND_LOW = 0.35   # below → Benign
RISK_BAND_HIGH = 0.65  # above → Phishing
# between → Uncertain

# Combined feature order (must match training + inference)
COMBINED_FEATURE_NAMES = URL_FEATURE_NAMES + HTML_FEATURE_NAMES

APP_TITLE = "Intelligent URL Threat Analyzer"
APP_ICON = "🛡️"
PAGE_LAYOUT = "wide"

# Exact tab names required by the specification
TAB_NAMES = [
    "Dashboard",
    "URL Threat Analyzer",
    "Threat Evidence & Explanation",
    "Dataset Explorer",
    "Threat Analytics",
    "Prediction History",
    "Model Performance",
    "About, Dataset & Methodology",
]

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MAX_HTML_PREVIEW_CHARS = 5000
MAX_URL_LENGTH = 2048

DISCLAIMER_BENIGN = (
    "A benign prediction does not guarantee that the website is safe. "
    "Always exercise caution and verify the site independently."
)
DISCLAIMER_PHISHING = (
    "A phishing prediction may be incorrect. "
    "This tool is an educational decision-support system, not a definitive security verdict."
)
RESPONSIBLE_USE_NOTE = (
    "This application is intended solely for defensive anti-phishing research "
    "and educational purposes. Do not use predictions to harass, target, or "
    "perform unauthorized actions against any website or individual."
)