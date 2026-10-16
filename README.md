<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Space+Grotesk&amp;weight=700&amp;size=34&amp;duration=3200&amp;pause=1000&amp;color=3B82F6&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=100&amp;lines=Before+the+click%2C+there+is+a+question.;What+can+the+link+tell+us%3F" alt="Intelligent URL Threat Analyzer: before clicking a suspicious phishing link, inspect its signals." />
  <br>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&amp;logoColor=white" alt="Python 3.10 or newer" />
  <img src="https://img.shields.io/badge/Streamlit-analysis%20app-FF4B4B?logo=streamlit&amp;logoColor=white" alt="Streamlit URL threat analysis application" />
  <img src="https://img.shields.io/badge/ML-classical%20models-6C63FF" alt="Classical machine learning models" />
  <img src="https://img.shields.io/badge/Database-MongoDB-47A248?logo=mongodb&amp;logoColor=white" alt="MongoDB data persistence" />
  <img src="https://img.shields.io/badge/Dataset-PhreshPhish-2E8B57" alt="PhreshPhish phishing URL dataset" />
  <img src="https://img.shields.io/badge/Features-53-0A7EA4" alt="53 deterministic URL and HTML features" />
</div>

<br>

<div align="center">
  <b>Intelligent_URL_Threat_analyzer</b><br>
  Inspect the link. Review the evidence. Keep the decision human.
</div>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=The+moment+before+the+click" alt="The moment before the click: story and motivation for a phishing URL threat analyzer" /></h2>

A message arrives with a link that looks familiar. The wording is urgent, the destination is one click away, and there is little time to decide. That is exactly when a closer look matters. A URL is a small artifact, but its hostname, path, and wording may preserve clues about the page waiting behind it.

**Intelligent_URL_Threat_analyzer** begins with a practical question: *before following a suspicious link, what can we learn from the link itself?* The answer is not certainty. It is a structured inspection: extract measurable characteristics, compare them with labeled examples, and show the observations so a person can decide what deserves further investigation.

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Why+phishing+links+matter" alt="Why phishing links matter: phishing URL analysis and defensive threat context" /></h2>

Phishing uses deception to move a person from a trusted context—an inbox, a message, a familiar brand—to a destination controlled by someone else. The link is often the transition point. Its appearance can imitate a legitimate service, while subtle differences in domain structure or path text may be worth reviewing.

This project focuses on that transition because it is concrete and inspectable. HTTPS does not establish trust, suspicious-looking text does not establish guilt, and a model cannot observe intent from a URL alone. The objective is to support cautious review, not to replace it with an automated verdict.

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=What+the+analyzer+observes" alt="What the phishing URL analyzer observes: URL input, optional HTML, model prediction, and evidence" /></h2>

The Streamlit application accepts an HTTP or HTTPS URL, optional HTML supplied by the user, and a selected saved classifier. It validates the URL, derives URL and HTML features, runs inference, and displays a class, probability where the model supports it, a risk band, and non-zero feature evidence.

The application does **not** request the destination, fetch its HTML, follow redirects, render JavaScript, inspect DNS or TLS, or query a live reputation service. Optional HTML must already be available to the user through an authorized process. This boundary is central to interpreting the output: the model analyzes submitted material, not the current live website.

<div align="center">
  <img src="https://img.shields.io/badge/Input-HTTP%20%2F%20HTTPS-2563EB" alt="Supported URL input schemes: HTTP and HTTPS" />
  <img src="https://img.shields.io/badge/Live%20fetching-Disabled-555555" alt="The analyzer does not fetch the live URL" />
  <img src="https://img.shields.io/badge/HTML-Optional-0A7EA4" alt="User-supplied HTML is optional" />
</div>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=The+dataset%3A+PhreshPhish" alt="PhreshPhish dataset: labeled benign and phishing URL examples used by the analyzer" /></h2>

The project uses [PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish), identified by the dataset ID `phreshphish/phreshphish`. Its source labels are retained as `benign` and `phish`, then mapped to two numeric classes for learning. The dataset provides URL records and associated fields, including HTML where available.

Ingestion streams records from Hugging Face into local or self-hosted MongoDB and upserts them by SHA-256, so repeated ingestion does not simply append duplicate copies. The project identifies the dataset as [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); use the dataset card and [paper](https://arxiv.org/abs/2507.10854) for provenance and attribution.

The evaluated sample contains **1,000 records**: **594 benign (59.4%)** and **406 phish (40.6%)**. A stratified split allocated **800 records for training** and **200 for testing**. The test subset contains **119 benign** and **81 phish** records. These counts describe the experiment, not the total size of PhreshPhish.

<div align="center">
  <a href="https://huggingface.co/datasets/phreshphish/phreshphish"><img src="https://img.shields.io/badge/Hugging%20Face-PhreshPhish-FFD21E?logo=huggingface&amp;logoColor=black" alt="Open the PhreshPhish dataset on Hugging Face" /></a>
  <img src="https://img.shields.io/badge/Labels-benign%20%7C%20phish-355C7D" alt="PhreshPhish labels: benign and phish" />
  <a href="https://creativecommons.org/licenses/by/4.0/"><img src="https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey" alt="PhreshPhish dataset license: Creative Commons Attribution 4.0" /></a>
</div>

```mermaid
pie showData
    title Label distribution in the evaluated 1,000-record sample
    "Benign — 59.4%" : 594
    "Phish — 40.6%" : 406
```

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=From+raw+input+to+53+signals" alt="Phishing detection methodology: 34 URL features and 19 HTML features form a 53-feature vector" /></h2>

The current inference contract is a fixed-order vector of **53 deterministic numeric features**. The URL extractor contributes **34 features** covering URL, host, path, and query lengths; punctuation; IP-address hosts; HTTPS; subdomain depth; shortened domains; suspicious TLD heuristics; and credential- or finance-related keywords.

The HTML extractor contributes **19 features** covering forms, input types, password fields, links, images, scripts, iframes, titles, metadata, favicons, login-form patterns, and selected JavaScript cues. When HTML is absent, these page features are zero-filled. Extractors are shared across training and inference so feature order does not drift between the offline experiment and the running application.

These values encode observations, not intent. A password input is common on legitimate services; a suspicious TLD is not proof of phishing; and the absence of a heuristic signal is not evidence of safety.

```mermaid
flowchart LR
    U[Validated URL] --> UF[34 URL features]
    H[Optional supplied HTML] --> HF[19 HTML features]
    UF --> V[Ordered 53-value vector]
    HF --> V
    V --> M[Saved classifier]
    M --> O[Class, probability if supported, risk band]
    V --> E[Observed feature evidence]
    E --> O
```

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Six+models%2C+one+shared+question" alt="Six classical machine learning models evaluated for phishing URL classification" /></h2>

The offline bench compares Logistic Regression, Linear SVC, Random Forest, Extra Trees, Histogram Gradient Boosting, and XGBoost on the URL-plus-HTML feature matrix. This gives the experiment linear, bagged-tree, and boosted-tree approaches to compare; it does not imply every model performs equally well or that one algorithm is universally best.

Model fitting and selection happen offline. The Streamlit application loads saved model artifacts and their metadata; it does not retrain at startup. Metadata preserves the label mapping, ordered feature names, model version, and threshold needed to interpret inference. Separate text experiments examine word/character TF-IDF, bag-of-words, and lexical features; those representations are not connected to the current app inference path.

<div align="center">
  <img src="https://img.shields.io/badge/Logistic%20Regression-linear-6C63FF" alt="Logistic Regression linear classifier" />
  <img src="https://img.shields.io/badge/Linear%20SVC-margin%20based-6C63FF" alt="Linear Support Vector Classifier" />
  <img src="https://img.shields.io/badge/Random%20Forest-bagged%20trees-2E8B57" alt="Random Forest classifier" />
  <img src="https://img.shields.io/badge/Extra%20Trees-randomized%20trees-2E8B57" alt="Extra Trees classifier" />
  <img src="https://img.shields.io/badge/Histogram%20GB-boosted%20trees-0A7EA4" alt="Histogram Gradient Boosting classifier" />
  <img src="https://img.shields.io/badge/XGBoost-boosted%20trees-0A7EA4" alt="XGBoost classifier" />
</div>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Evaluation%3A+what+the+saved+run+says" alt="Phishing URL model evaluation metrics from the saved Random Forest test report" /></h2>

At the default threshold of **0.5**, the saved Random Forest test report gives **0.950 accuracy**, **0.948 balanced accuracy**, **0.938 precision for phish**, **0.938 recall for phish**, **0.938 phish F1**, **0.992 ROC-AUC**, and **0.988 PR-AUC**. Its test confusion matrix is `[[114, 5], [5, 76]]`, with actual labels as rows (`benign`, `phish`) and predicted labels as columns.

| Evaluation context | Saved value |
| --- | ---: |
| Training records | 800 |
| Test records | 200 |
| Test class support | 119 benign, 81 phish |
| Test accuracy | 0.950 |
| Test balanced accuracy | 0.948 |
| Test phishing recall | 0.938 |
| Test phishing F1 | 0.938 |
| Test ROC-AUC / PR-AUC | 0.992 / 0.988 |

Across the **200 test cases**, the model classified **190 correctly (95%)** and **10 incorrectly (5%)**. Five benign records were flagged as phish, a **4.2% false-positive rate** among the 119 benign cases; five phishing records were classified as benign, a **6.2% false-negative rate** among the 81 phishing cases. Those errors have different consequences, so accuracy alone is not enough.

This is a small experiment—not a deployment benchmark, a guarantee of detection, or a measurement of all URLs in the wild. Performance can change with sampling, distribution shift, labels, and threshold selection. Read the metrics alongside the sample size and class counts rather than as a stand-alone promise.

```mermaid
pie showData
    title Random Forest test outcomes — 200 records
    "Correct benign: 114" : 114
    "False alarms: 5" : 5
    "Missed phishing: 5" : 5
    "Correct phishing: 76" : 76
```

<div align="center">
  <img src="https://img.shields.io/badge/Test%20accuracy-95.0%25-2E8B57" alt="Saved Random Forest test accuracy: 95.0 percent" />
  <img src="https://img.shields.io/badge/Balanced%20accuracy-94.8%25-2E8B57" alt="Saved Random Forest balanced accuracy: 94.8 percent" />
  <img src="https://img.shields.io/badge/Phish%20recall-93.8%25-6C63FF" alt="Saved Random Forest phishing recall: 93.8 percent" />
  <img src="https://img.shields.io/badge/PR--AUC-0.988-0A7EA4" alt="Saved Random Forest precision-recall area under curve: 0.988" />
</div>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Reading+the+prediction+carefully" alt="How to interpret phishing prediction labels, probability scores, and risk bands" /></h2>

The classifier returns a binary label: `benign` or `phish`. If the selected estimator exposes probability estimates, the application uses the saved threshold—normally **0.5**—to determine that class. The user interface separately maps the estimated phishing probability to risk bands: below **0.35** is **Benign**, above **0.65** is **Phishing**, and the interval from **0.35** through **0.65** is **Uncertain**.

Because class threshold and risk-band cutoffs are different, a binary class and displayed risk band can disagree. Linear SVC has no probability output in the current inference path, so its result cannot provide `P(phish)`; the risk display falls back to its predicted class. The application does not claim calibrated probabilities. Evidence lists observed non-zero features; it does not establish which feature caused a decision or prove a site's intent.

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=The+analyst%27s+path+through+the+app" alt="Analyst workflow for phishing URL triage using the Streamlit analyzer" /></h2>

The analyst workflow starts with a URL that should not be opened merely to satisfy curiosity. The user submits the address, optionally adds HTML already obtained with authorization, selects a model, and reviews both the output and its evidence. MongoDB availability controls dataset-backed pages and prediction-history persistence; the sidebar reports database status.

```mermaid
flowchart TD
    A[Receive suspicious URL] --> B[Do not open solely for analysis]
    B --> C[Submit URL to analyzer]
    C --> D{Authorized HTML available?}
    D -- Yes --> E[Paste supplied HTML]
    D -- No --> F[Continue with URL features]
    E --> G[Extract fixed-order feature vector]
    F --> G
    G --> H[Run selected saved model]
    H --> I[Review class, risk band, and evidence]
    I --> J[Verify independently and follow security procedure]
    H -. optional history .-> K[(MongoDB)]
```

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=The+research+workflow+behind+the+model" alt="Offline PhreshPhish data ingestion, feature engineering, machine learning, and artifact export workflow" /></h2>

The model lifecycle is intentionally separate from live analysis. Dataset review and ingestion feed exploration and feature extraction; candidate models are trained and evaluated offline; model artifacts and metadata are then prepared for interactive inference. Bounded samples are useful when validating an experiment. MongoDB must be running for ingestion and database-backed training.

```mermaid
flowchart LR
    A[PhreshPhish stream] --> B[Schema and label audit]
    B --> C[MongoDB upsert]
    C --> D[Explore and clean]
    D --> E[URL and HTML features]
    E --> F[Text representation experiments]
    E --> G[Train classical models]
    G --> H[Evaluate and select]
    H --> I[Prepare model artifacts]
    I --> J[Interactive inference]
    C <--> M[(MongoDB)]
    J -. prediction history .-> M
```

The text-representation comparison is a separate research track; the deployed analyzer uses the URL-plus-HTML feature contract. Keeping those paths distinct makes it clear which experiment produced the model used for a prediction.

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Two+paths%2C+one+consistent+feature+contract" alt="Architecture separating offline ML training from online Streamlit URL analysis" /></h2>

Offline training produces serialized models, metadata, evaluation results, and an artifact inventory. Online inference validates input, invokes the same feature definitions in the training order, loads a saved model, and returns the prediction with observed evidence. It does not fit models during app startup or prediction.

MongoDB stores source records, derived features, model metadata, evaluation summaries, and optional prediction history. It is configured for local or self-hosted use. The exported experiment identifies Random Forest as selected, while the analyzer initially prefers Logistic Regression when available. Choose the model in the interface rather than assuming those defaults are synchronized.

```mermaid
flowchart LR
    subgraph Offline["Offline experiment"]
        DS[PhreshPhish] --> ING[Ingest and feature engineering]
        ING --> TR[Train and evaluate]
        TR --> ART[(Joblib plus JSON artifacts)]
    end
    subgraph Online["Interactive analysis"]
        IN[URL and optional HTML] --> VAL[Validate and extract]
        VAL --> INF[Load artifact and infer]
        ART --> INF
        INF --> RES[Prediction plus evidence]
    end
    ING <--> DB[(MongoDB)]
    RES -. optional history .-> DB
```

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=2563EB&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=From+research+bench+to+careful+use" alt="Responsible use of an offline-trained Intelligent URL Threat Analyzer" /></h2>

The application is designed for Python **3.10 or newer**, Streamlit, classical machine-learning estimators, and optional local or self-hosted MongoDB. Model inference requires saved model artifacts. MongoDB enables dataset-backed views, ingestion, and prediction-history persistence. The interface is an analyst-facing view over offline-trained models, not a live protective gateway.

**Use the result as triage, never as authorization to click.** A Benign prediction is not a safety guarantee; a Phishing prediction is not proof of intent. Do not submit data unless you are authorized to handle it. Prediction history may persist in MongoDB. Verify consequential decisions using independent evidence and established security procedures.

<div align="center">
  <img src="https://img.shields.io/badge/Decision%20support-Not%20a%20verdict-F59E0B" alt="Decision support only: predictions are not definitive verdicts" />
  <img src="https://img.shields.io/badge/Live%20site%20inspection-Not%20performed-555555" alt="The application does not inspect or fetch live websites" />
</div>

<br>

<div align="center">
  <a href="https://huggingface.co/datasets/phreshphish/phreshphish"><img src="https://img.shields.io/badge/Explore%20the%20data-PhreshPhish-FFD21E?logo=huggingface&amp;logoColor=black" alt="Explore the PhreshPhish dataset" /></a>
  <a href="https://arxiv.org/abs/2507.10854"><img src="https://img.shields.io/badge/Read%20the%20research-Paper-2563EB" alt="Read the PhreshPhish research paper" /></a>
</div>
