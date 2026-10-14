# Feature List — Intelligent URL Threat Analyzer

> What the models actually see. Not magic — measurements.

Every signal below is **deterministic**: same URL/HTML in → same numbers out.  
Training and the Streamlit app share the same extractors so inference does not drift from what was learned offline.

Dataset labels stay **`benign`** / **`phish`**

---

## 1. URL structural features

Parsed from the URL string only. Fast, no network fetch.

| Feature | What it measures | Why it can matter |
|---------|------------------|-------------------|
| `url_length` | Total character length | Very long URLs often hide noise or redirects |
| `hostname_length` | Length of host (netloc) | Odd hostnames show up in campaigns |
| `path_length` | Length of path | Deep or padded paths appear in phishing kits |
| `query_length` | Length of query string | Heavy query strings can carry tracking or decoys |
| `num_dots` | Count of `.` | Extra dots → more subdomains or weird hosts |
| `num_hyphens` | Count of `-` | Hyphen-stuffed domains are a common pattern |
| `num_underscores` | Count of `_` | Less common in legit brand domains |
| `num_slashes` | Count of `/` | Path depth / structure |
| `num_question_marks` | Count of `?` | Multiple query starts look malformed |
| `num_equals` | Count of `=` | Query parameter density |
| `num_at` | Count of `@` | `@` in URLs is a classic obfuscation trick |
| `num_ampersand` | Count of `&` | Parameter chaining |
| `num_exclamation` | Count of `!` | Rare in clean URLs |
| `num_tilde` | Count of `~` | Sometimes used in shady paths |
| `num_comma` | Count of `,` | Unusual in standard URLs |
| `num_plus` | Count of `+` | Encoding / padding signals |
| `num_asterisk` | Count of `*` | Rare; often noise |
| `num_hash` | Count of `#` | Fragments / client-side routing |
| `num_dollar` | Count of `$` | Uncommon in normal links |
| `num_percent` | Count of `%` | Percent-encoding density |
| `has_ip_address` | Host looks like IPv4 | Raw IPs instead of names are suspicious |
| `has_https` | Scheme is `https` | Absence is a weak negative signal, not proof |
| `has_www` | Host starts with `www.` | Mild structural cue |
| `is_shortened` | Known shortener domain | Hides final destination |
| `num_subdomains` | Rough subdomain depth | Deep subdomain chains are a red flag |
| `tld_length` | Length of TLD token | Odd TLDs often pair with abuse |
| `has_suspicious_tld` | TLD in a small heuristic set (e.g. tk, ml, xyz, top, click, …) | Cheap/abused namespaces |
| `has_login_keyword` | login / signin / logon-style tokens in URL | Credential-harvest bait |
| `has_secure_keyword` | secure / ssl / verify-style tokens | Fake trust language |
| `has_account_keyword` | account / user-style tokens | Account takeover themes |
| `has_update_keyword` | update / confirm / validation-style tokens | “Please update” lures |
| `has_verify_keyword` | verify / auth-style tokens | Verification urgency |
| `has_bank_keyword` | bank / finance / wallet-style tokens | Financial impersonation |
| `has_paypal_keyword` | paypal-style tokens | Brand spoofing |

**Implementation:** `src/features/url_features.py` → `extract_url_features()` / `URLFeatureExtractor`.

---

## 2. HTML / page features

Extracted with BeautifulSoup (lxml, fallback to `html.parser`). Malformed markup should not crash the pipeline. HTML is length-capped before parsing for memory safety.

| Feature | What it measures | Why it can matter |
|---------|------------------|-------------------|
| `html_length` | Characters of HTML considered | Extreme size or emptiness both informative |
| `num_forms` | `<form>` count | Credential forms are central to many phishing pages |
| `num_inputs` | `<input>` count | Form complexity |
| `num_password_inputs` | `type=password` inputs | Direct credential collection signal |
| `num_hidden_inputs` | `type=hidden` inputs | Tokens, traps, or kit fingerprints |
| `num_links` | Anchors with `href` | Overall linkage density |
| `num_external_links` | Links off-site | Heavy external linking can signal kits or cloaking |
| `num_internal_links` | Relative / same-site style links | Balance vs external |
| `num_images` | `<img>` count | Layout richness / decoy assets |
| `num_scripts` | `<script>` count | Script-heavy pages warrant caution |
| `num_iframes` | `<iframe>` count | Often used for embedding or cloaking |
| `has_title` | `<title>` present | Missing title is a weak quality signal |
| `title_length` | Length of title text | Empty or tiny titles on “bank” pages look off |
| `has_meta_description` | Meta description present | Basic page completeness |
| `num_meta_tags` | Count of `<meta>` | Structure / generator footprints |
| `has_favicon` | Link rel icon | Missing favicon on “official” brands is a mild cue |
| `num_buttons` | Submit/button-like controls | CTA density |
| `has_login_form` | Form HTML suggests login/password/username | Stronger than URL keywords alone |
| `has_suspicious_js` | Light patterns (e.g. `eval`, `document.write`, location assigns) | Obfuscation / injected behavior heuristics |

**Implementation:** `src/features/html_features.py` → `extract_html_features()` / `HTMLFeatureExtractor`.

**Important:** These are **observations**, not proof. Legitimate sites also have password fields and scripts.

---

## 3. Text / NLP representations

Used in offline NLP experiments (≥4 approaches). Can be applied to URL text, title, or concatenated page text.

| Approach | Method key | What it is |
|----------|------------|------------|
| TF-IDF (word) | `tfidf_word` | Word n-grams with TF-IDF weighting |
| TF-IDF (char) | `tfidf_char` | Character n-grams (robust to noise/obfuscation) |
| Bag-of-Words | `bow` | Raw term counts (CountVectorizer) |
| Lexical stats | `lexical` | Length, digit/letter/special ratios, entropy, word counts, uppercase ratio |
| Union (optional) | `union` | TF-IDF word + lexical stacked |

**Lexical stats detail**

| Name | Meaning |
|------|---------|
| `lex_length` | Character length |
| `lex_num_digits` / `lex_digit_ratio` | Digit mass |
| `lex_num_letters` / `lex_letter_ratio` | Letter mass |
| `lex_num_spaces` / `lex_space_ratio` | Whitespace |
| `lex_num_special` / `lex_special_ratio` | Non-alnum symbols |
| `lex_entropy` | Character-level entropy |
| `lex_avg_word_len` | Average token length |
| `lex_num_words` | Token count |
| `lex_num_unique_words` | Vocabulary size in the snippet |
| `lex_uppercase_ratio` | SHOUTY text share |

**Implementation:** `src/features/text_features.py` → `TextFeatureExtractor`, vectorizer builders, `lexical_stats()`.

---

## 4. How features are combined at inference

For a typical URL analysis in the app:

1. Run **URL** extractors on the normalized URL.  
2. Run **HTML** extractors if the user pasted markup (otherwise zeros).  
3. Concatenate into one numeric vector in a **fixed column order** (see `URL_FEATURE_NAMES` + `HTML_FEATURE_NAMES` in `config/constants.py`).  
4. Feed the vector to the loaded classical model.  
5. Surface non-zero signals in the **Threat Evidence** tab as “what was observed,” separate from the predicted class.

Text vectorizers are primarily exercised in offline script `05_nlp_experiments.py` and can be wired into custom pipelines the same way.

---

## 5. Design rules (so features stay honest)

- **No live fetch by default** — features come from the submitted URL string and optional user-supplied HTML, or from dataset rows already in MongoDB.  
- **Truncation** — huge HTML is cut before parse/storage so one page cannot OOM the process.  
- **Same code path** — offline matrix building and online `predict_url` call the same functions.  
- **No single feature = guilty** — models combine many weak signals; the UI says so explicitly.  
- **Labels** — supervised target is PhreshPhish `label` only after validation (`benign` / `phish`).

---

## 6. Where the names live

| Constant | File |
|----------|------|
| `URL_FEATURE_NAMES` | `config/constants.py` |
| `HTML_FEATURE_NAMES` | `config/constants.py` |
| Extractors | `src/features/*.py` |
| Inference assembly | `src/models/predict.py` |
| Offline matrix | `scripts/ml_feature_utils.py` |

When you add a feature, append it to the constant list **and** the extractor so training and serving stay aligned.

---

*Features are evidence, not verdicts. The model votes; you still think.*
