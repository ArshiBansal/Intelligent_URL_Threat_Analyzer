# Evaluation Report — Intelligent URL Threat Analyzer

> Train offline. Measure honestly. Never invent metrics in the UI.

This document describes **how** models are evaluated, **what** is reported, and **how** a final model is chosen. Numbers below are the **methodology and placeholders**; fill in actual scores after you run scripts `06`–`08` on your machine.

Dataset: **PhreshPhish** (`phreshphish/phreshphish`) · Labels: `benign` / `phish`  
Stack: classical ML (scikit-learn + XGBoost) ·  NLP (TF-IDF, Bag-of-Words, lexical)

---

## 1. Evaluation philosophy

1. **Reproducible splits** — stratified train/validation/test (or train/test) with a fixed `random_state`.  
2. **Multiple metrics** — accuracy alone is not enough under class imbalance.  
3. **Per-class truth** — phishing recall and precision matter as much as overall F1.  
4. **Saved, not improvised** — the Model Performance tab only displays metrics written by offline scripts.  
5. **Threshold awareness** — default 0.5 is a starting point; best-F1 threshold is recorded when probabilities exist.

If a benign score looks comforting, remember: **it is not a safety guarantee**. If a phish score looks alarming, remember: **it can be wrong**.

---

## 2. What gets measured

### Classification (required)

| Metric | Role |
|--------|------|
| Precision / Recall / F1 | Overall quality on the positive (phish) framing used in reporting |
| Per-class precision, recall, F1 | Separate story for `benign` and `phish` |
| Confusion matrix | TN / FP / FN / TP — where the model actually fails |
| Balanced accuracy | Fairer when classes are uneven |
| Accuracy | Reported, but not the hero metric |

### Class imbalance (required)

| Metric | Role |
|--------|------|
| PR curve / Average Precision (PR-AUC) | Focuses on the positive class under skew |
| ROC-AUC | Supplementary ranking quality |

### Threshold choice

| Check | Role |
|-------|------|
| Default threshold (0.5) | Baseline operating point |
| Best-F1 threshold | Empirically better cut on the validation/test probabilities |
| FP vs FN trade-off | Document why you preferred one side of the error |

### Robustness & efficiency (as supported)

| Check | Role |
|-------|------|
| Missing / empty HTML | URL-only path still produces a vector |
| Duplicates / leakage | Upsert by `sha256`; no random row reuse across splits in matrix builders |
| Inference latency | Feature extract + predict should stay interactive in Streamlit |
| DB query latency | Paginated reads only — never full-collection loads in the UI |

---

## 3. Models under comparison

Minimum of **four** classical approaches (spec):

| Model key | Algorithm |
|-----------|-----------|
| `logistic_regression` | Logistic Regression (balanced class weight) |
| `random_forest` | Random Forest |
| `xgboost` | XGBoost classifier |
| `gradient_boosting` | Gradient Boosting |

Text-side experiments (script `05`) additionally compare **≥4** representations: TF-IDF word, TF-IDF char, bag-of-words, lexical stats (optional union).

Feature matrix for the main ML scripts: **URL features + HTML features** (fixed order from `config/constants.py`), built by `scripts/ml_feature_utils.py`.

---

## 4. How to reproduce results

```bash
# Data already in MongoDB (capped ingest recommended on laptops)
python scripts/03_clean_and_explore.py
python scripts/04_feature_engineering.py --max-records 20000

# NLP comparison (optional but required by methodology)
python scripts/05_nlp_experiments.py --max-records 8000

# Train + evaluate ≥4 models; write joblib + eval JSON
python scripts/06_ml_experiments.py --max-records 15000 --save-artifacts

# Select winner; optional Mongo registration
python scripts/07_evaluate_and_select.py --metric f1
# python scripts/07_evaluate_and_select.py --prefer xgboost --register-mongo

# Manifest + optional promote to latest_*
python scripts/08_export_artifacts.py --promote
```

Artifacts land under:

- `artifacts/models/*.joblib`  
- `artifacts/metadata/eval_*.json`  
- `data/reports/ml_comparison.json`  
- `data/reports/model_selection.json`  
- `data/reports/nlp_comparison.json`  

Streamlit **Model Performance** reads these files / Mongo evaluation collection — it does not retrain.

---

## 5. Results template (fill after your run)

### 5.1 Data snapshot

| Item | Value |
|------|--------|
| Split source | MongoDB `phreshphish_records` (from HF streaming ingest) |
| Samples used (matrix) | _e.g. 15,000_ |
| Feature dimension | _len(URL_FEATURE_NAMES) + len(HTML_FEATURE_NAMES)_ |
| Class counts (y) | benign: ___ · phish: ___ |
| Train / test ratio | 80 / 20 stratified |

### 5.2 Test-set leaderboard (example layout)

| Model | Accuracy | Balanced acc | Precision | Recall | F1 | ROC-AUC | PR-AUC | F1 (phish) | Recall (phish) |
|-------|----------|--------------|-----------|--------|-----|---------|--------|------------|----------------|
| logistic_regression | — | — | — | — | — | — | — | — | — |
| random_forest | — | — | — | — | — | — | — | — | — |
| xgboost | — | — | — | — | — | — | — | — | — |
| gradient_boosting | — | — | — | — | — | — | — | — | — |

_Paste numbers from `data/reports/ml_comparison.json` or `model_selection.json`._

### 5.3 Selected model

| Field | Value |
|-------|--------|
| Selected model | _e.g. random_forest_ |
| Selection metric | _e.g. f1_ |
| Version | `v1.0.0` (or your stamp) |
| Default threshold | `0.5` |
| Best-F1 threshold (if computed) | — |
| Notes | _Why this model: stability, phish recall, speed, …_ |

### 5.4 Confusion matrix (test, selected model)

```
                 Pred benign    Pred phish
True benign         TN              FP
True phish          FN              TP
```

_Replace TN/FP/FN/TP with integers from the eval JSON._

### 5.5 Error sketch (qualitative)

| Error type | What you tend to see | Mitigation idea |
|------------|----------------------|-----------------|
| False positive | Aggressive brand keywords in legit URLs; shortener links | Threshold tuning; more URL context |
| False negative | Sparse HTML; clean-looking path on a bad host | Encourage optional HTML paste; richer host signals |
| URL-only rows | Weaker page signals | Document confidence drop when HTML missing |

---

## 6. NLP experiment summary (template)

From `05_nlp_experiments.py` / `data/reports/nlp_comparison.json`:

| Representation | Feature dim | Test F1 | ROC-AUC | Notes |
|----------------|-------------|---------|---------|--------|
| tfidf_word | — | — | — | — |
| tfidf_char | — | — | — | — |
| bow | — | — | — | — |
| lexical | — | — | — | cheap, strong baseline |

Main production path in the app remains **URL + HTML numeric features**; text experiments justify the “≥4 NLP approaches” requirement and inform future pipelines.

---

## 7. Limitations (read before celebrating a high F1)

- Sample size on a laptop is a **subset** of full PhreshPhish train/test.  
- HTML is **truncated** for memory safety; some page signal is lost.  
- No default live crawl — live sites can differ from dataset snapshots.  
- Keyword and form heuristics fire on **legitimate** login pages too.  
- Class balance in your Mongo sample may not match the full published corpus.  
- Thresholds tuned on one split can drift if the traffic mix changes.

---

## 8. Responsible use (evaluation edition)

- Report **phish recall** alongside overall accuracy so “looks great” does not hide missed attacks.  
- Report **benign precision** so users know how often alarms are noise.  
- Do not ship a model that only looks good on training data — check the train/test gap in `full_evaluation_report`.  
- Keep PhreshPhish attribution and CC-BY-4.0 obligations when publishing numbers.

---

## 9. Where code and outputs live

| Piece | Location |
|-------|----------|
| Train / save | `src/models/train.py`, `scripts/06_ml_experiments.py` |
| Metrics | `src/models/evaluate.py` |
| Compare ML / text | `src/models/compare.py`, `scripts/05_nlp_experiments.py` |
| Select | `scripts/07_evaluate_and_select.py` |
| Manifest | `scripts/08_export_artifacts.py` → `artifacts/manifest.json` |
| UI display | Streamlit tab **Model Performance** |

---

## 10. Changelog

| Date | Note |
|------|------|
| _YYYY-MM-DD_ | Initial methodology doc; results pending local `06`/`07` run |
| _YYYY-MM-DD_ | Filled leaderboard + selected model after experiment |

---

*Measure twice. Deploy once. Still tell the user the score is not certainty.*
