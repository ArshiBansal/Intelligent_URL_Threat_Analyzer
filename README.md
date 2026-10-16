<div align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Space+Grotesk&amp;weight=700&amp;size=34&amp;duration=3200&amp;pause=1000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=100&amp;lines=Before+the+click%2C+there+is+a+question.;What+can+the+link+tell+us%3F" alt="Intelligent URL Threat Analyzer: before clicking a suspicious phishing link, inspect its signals." />
  <br>
  <img src="https://img.shields.io/badge/Python-3.10%2B-1D4ED8?logo=python&amp;logoColor=white" alt="Python 3.10 or newer" />
  <img src="https://img.shields.io/badge/Streamlit-analysis%20app-4C1D95?logo=streamlit&amp;logoColor=white" alt="Streamlit URL threat analysis application" />
  <img src="https://img.shields.io/badge/ML-classical%20models-5B21B6" alt="Classical machine learning models" />
  <img src="https://img.shields.io/badge/Database-MongoDB-1E3A8A?logo=mongodb&amp;logoColor=white" alt="MongoDB data persistence" />
  <img src="https://img.shields.io/badge/Dataset-PhreshPhish-312E81" alt="PhreshPhish phishing URL dataset" />
  <img src="https://img.shields.io/badge/Features-53-1E40AF" alt="53 deterministic URL and HTML features" />
</div>

<br>

<div align="center">
  <b>Intelligent_URL_Threat_analyzer</b><br>
  Inspect the link. Review the evidence. Keep the decision human.
</div>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=The+moment+before+the+click" alt="The moment before the click: story and motivation for a phishing URL threat analyzer" /></h2>

<p align="justify">A message arrives with a link that looks familiar. The wording is urgent, the destination is one click away, and there is little time to decide. That is exactly when a closer look matters. A URL is a small artifact, but its hostname, path, and wording may preserve clues about the page waiting behind it.</p>

<p align="justify"><b>Intelligent_URL_Threat_analyzer</b> begins with a practical question: <i>before following a suspicious link, what can we learn from the link itself?</i> The answer is not certainty. It is a structured inspection: extract measurable characteristics, compare them with labeled examples, and show the observations so a person can decide what deserves further investigation.</p>

> “Pause before the click” is not just a slogan here; it is the whole threat model in miniature.

<p align="center"><i>The link says “verify now.” The analyst says “let's verify that.”</i></p>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Why+phishing+links+matter" alt="Why phishing links matter: phishing URL analysis and defensive threat context" /></h2>

Phishing uses deception to move a person from a trusted context—an inbox, a message, a familiar brand—to a destination controlled by someone else. The link is often the transition point. Its appearance can imitate a legitimate service, while subtle differences in domain structure or path text may be worth reviewing.

<p align="justify">This project focuses on that transition because it is concrete and inspectable. HTTPS does not establish trust, suspicious-looking text does not establish guilt, and a model cannot observe intent from a URL alone. The objective is to support cautious review, not to replace it with an automated verdict.</p>

<blockquote>
  <i>A padlock says the connection is encrypted. It does not tell you who is on the other end.</i>
</blockquote>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=What+the+analyzer+observes" alt="What the phishing URL analyzer observes: URL input, optional HTML, model prediction, and evidence" /></h2>

<p align="justify">The Streamlit application accepts an HTTP or HTTPS URL, optional HTML supplied by the user, and a selected saved classifier. It validates the URL, derives URL and HTML features, runs inference, and displays a class, probability where the model supports it, a risk band, and non-zero feature evidence.</p>

The application does **not** request the destination, fetch its HTML, follow redirects, render JavaScript, inspect DNS or TLS, or query a live reputation service. Optional HTML must already be available to the user through an authorized process. This boundary is central to interpreting the output: the model analyzes submitted material, not the current live website.

<div align="center">
  <img src="https://img.shields.io/badge/%F0%9F%94%97%20Input-HTTP%20%2F%20HTTPS-1D4ED8" alt="Link input supports HTTP and HTTPS schemes" />
  <img src="https://img.shields.io/badge/%F0%9F%9B%A1%20Live%20fetching-Disabled-111827" alt="The analyzer does not fetch the live URL" />
  <img src="https://img.shields.io/badge/%F0%9F%A7%BE%20HTML-Optional-3730A3" alt="User-supplied HTML is optional" />
</div>

> [!IMPORTANT]
> No live website is fetched. If HTML is not already available to you through an authorized process, analyze the URL alone—do not visit a suspicious destination just to provide more input.

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=The+dataset%3A+PhreshPhish" alt="PhreshPhish dataset: labeled benign and phishing URL examples used by the analyzer" /></h2>

The project uses [PhreshPhish](https://huggingface.co/datasets/phreshphish/phreshphish), identified by the dataset ID `phreshphish/phreshphish`. Its source labels are retained as `benign` and `phish`, then mapped to two numeric classes for learning. The dataset provides URL records and associated fields, including HTML where available.

Ingestion streams records from Hugging Face into local or self-hosted MongoDB and upserts them by SHA-256, so repeated ingestion does not simply append duplicate copies. The project identifies the dataset as [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); use the dataset card and [paper](https://arxiv.org/abs/2507.10854) for provenance and attribution.

The evaluated sample contains **1,000 records**: **594 benign (59.4%)** and **406 phish (40.6%)**. A stratified split allocated **800 records for training** and **200 for testing**. The test subset contains **119 benign** and **81 phish** records. These counts describe the experiment, not the total size of PhreshPhish.

<div align="center">
  <a href="https://huggingface.co/datasets/phreshphish/phreshphish"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Dataset-PhreshPhish-312E81" alt="Open the PhreshPhish dataset on Hugging Face" /></a>
  <img src="https://img.shields.io/badge/%F0%9F%8F%B7%20Labels-benign%20%7C%20phish-1E3A8A" alt="PhreshPhish labels: benign and phish" />
  <a href="https://creativecommons.org/licenses/by/4.0/"><img src="https://img.shields.io/badge/%F0%9F%93%9C%20License-CC%20BY%204.0-3730A3" alt="PhreshPhish dataset license: Creative Commons Attribution 4.0" /></a>
</div>

<div align="center">
  <img src="https://img.shields.io/badge/%E2%97%86%20BENIGN-594%20records%20%7C%2059.4%25-1E3A8A" alt="Benign: 594 records, 59.4 percent of evaluated sample" />
  <img src="https://img.shields.io/badge/%E2%97%86%20PHISH-406%20records%20%7C%2040.6%25-4C1D95" alt="Phish: 406 records, 40.6 percent of evaluated sample" />
</div>

<blockquote>
  <b>Sample, not census:</b> these 1,000 records describe the checked-in experiment, not the full PhreshPhish dataset and not the entire universe of phishing.
</blockquote>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=From+raw+input+to+53+signals" alt="Phishing detection methodology: 34 URL features and 19 HTML features form a 53-feature vector" /></h2>

The current inference contract is a fixed-order vector of **53 deterministic numeric features**. The URL extractor contributes **34 features** covering URL, host, path, and query lengths; punctuation; IP-address hosts; HTTPS; subdomain depth; shortened domains; suspicious TLD heuristics; and credential- or finance-related keywords.

The HTML extractor contributes **19 features** covering forms, input types, password fields, links, images, scripts, iframes, titles, metadata, favicons, login-form patterns, and selected JavaScript cues. When HTML is absent, these page features are zero-filled. Extractors are shared across training and inference so feature order does not drift between the offline experiment and the running application.

These values encode observations, not intent. A password input is common on legitimate services; a suspicious TLD is not proof of phishing; and the absence of a heuristic signal is not evidence of safety.

<p><b>Illustrative example—not a real threat report:</b> in <code>https://accounts.example.com/verify</code>, the analyzer can measure hostname structure, path, HTTPS, and keyword cues. The word “accounts” is a feature candidate, <mark>not a verdict</mark>. Authorized HTML, if available, contributes a separate set of measurements.</p>

```mermaid
%%{init: {'theme':'base','themeVariables': {'primaryColor':'#312E81','primaryTextColor':'#ffffff','primaryBorderColor':'#6D5BD0','lineColor':'#4F46E5','secondaryColor':'#1E3A8A','tertiaryColor':'#111827','background':'#ffffff','mainBkg':'#312E81','nodeBorder':'#6D5BD0','clusterBkg':'#111827','clusterBorder':'#4F46E5'}}}%%
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

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Six+models%2C+one+shared+question" alt="Six classical machine learning models evaluated for phishing URL classification" /></h2>

The offline bench compares Logistic Regression, Linear SVC, Random Forest, Extra Trees, Histogram Gradient Boosting, and XGBoost on the URL-plus-HTML feature matrix. This gives the experiment linear, bagged-tree, and boosted-tree approaches to compare; it does not imply every model performs equally well or that one algorithm is universally best.

Model fitting and selection happen offline. The Streamlit application loads saved model artifacts and their metadata; it does not retrain at startup. Metadata preserves the label mapping, ordered feature names, model version, and threshold needed to interpret inference. Separate text experiments examine word/character TF-IDF, bag-of-words, and lexical features; those representations are not connected to the current app inference path.

<div align="center">
  <img src="https://img.shields.io/badge/%F0%9F%A7%AE%20Logistic%20Regression-linear-5B21B6" alt="Logistic Regression linear classifier" />
  <img src="https://img.shields.io/badge/%F0%9F%93%90%20Linear%20SVC-margin%20based-3730A3" alt="Linear Support Vector Classifier" />
  <img src="https://img.shields.io/badge/%F0%9F%8C%B2%20Random%20Forest-bagged%20trees-1E3A8A" alt="Random Forest classifier" />
  <img src="https://img.shields.io/badge/%F0%9F%8C%B3%20Extra%20Trees-randomized%20trees-312E81" alt="Extra Trees classifier" />
  <img src="https://img.shields.io/badge/%E2%9A%99%EF%B8%8F%20Histogram%20GB-boosted%20trees-1D4ED8" alt="Histogram Gradient Boosting classifier" />
  <img src="https://img.shields.io/badge/%F0%9F%9A%80%20XGBoost-boosted%20trees-4C1D95" alt="XGBoost classifier" />
</div>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Evaluation%3A+what+the+saved+run+says" alt="Phishing URL model evaluation metrics from the saved Random Forest test report" /></h2>

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

> [!IMPORTANT]
> A **93.8% phishing recall** means this saved test run still missed phishing examples. In the 81 phishing test cases, **5 were missed**. High scores do not make a suspicious link safe to open.

<div align="center">
  <img src="https://img.shields.io/badge/%E2%9C%93%20Correct%20benign-114-1E3A8A" alt="114 benign test records correctly classified" />
  <img src="https://img.shields.io/badge/%E2%9C%93%20Correct%20phish-76-312E81" alt="76 phishing test records correctly classified" />
  <img src="https://img.shields.io/badge/%E2%9C%97%20False%20alarms-5-3730A3" alt="5 benign test records incorrectly flagged as phishing" />
  <img src="https://img.shields.io/badge/%E2%9C%97%20Missed%20phish-5-111827" alt="5 phishing test records incorrectly classified as benign" />
</div>

<div align="center">
  <img src="https://img.shields.io/badge/%F0%9F%8E%AF%20Accuracy-95.0%25-1D4ED8" alt="Saved Random Forest test accuracy: 95.0 percent" />
  <img src="https://img.shields.io/badge/%E2%9A%96%EF%B8%8F%20Balanced%20accuracy-94.8%25-3730A3" alt="Saved Random Forest balanced accuracy: 94.8 percent" />
  <img src="https://img.shields.io/badge/%F0%9F%94%8D%20Phish%20recall-93.8%25-4C1D95" alt="Saved Random Forest phishing recall: 93.8 percent" />
  <img src="https://img.shields.io/badge/%F0%9F%93%88%20PR--AUC-0.988-1E3A8A" alt="Saved Random Forest precision-recall area under curve: 0.988" />
</div>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Reading+the+prediction+carefully" alt="How to interpret phishing prediction labels, probability scores, and risk bands" /></h2>

The classifier returns a binary label: `benign` or `phish`. If the selected estimator exposes probability estimates, the application uses the saved threshold—normally **0.5**—to determine that class. The user interface separately maps the estimated phishing probability to risk bands: below **0.35** is **Benign**, above **0.65** is **Phishing**, and the interval from **0.35** through **0.65** is **Uncertain**.

Because class threshold and risk-band cutoffs are different, a binary class and displayed risk band can disagree. Linear SVC has no probability output in the current inference path, so its result cannot provide `P(phish)`; the risk display falls back to its predicted class. The application does not claim calibrated probabilities. Evidence lists observed non-zero features; it does not establish which feature caused a decision or prove a site's intent.

<p><b>Example:</b> an estimated phishing probability of <code>0.58</code> can fall into the <b>Uncertain</b> risk band even though it is above the classifier's default <code>0.5</code> threshold for the binary class. <mark>Different thresholds answer different questions.</mark></p>

<p><del>“The model said benign, so we're done.”</del> <i>Better:</i> “The model found fewer phishing-like signals; what independent evidence do we have?”</p>

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=The+analyst%27s+path+through+the+app" alt="Analyst workflow for phishing URL triage using the Streamlit analyzer" /></h2>

The analyst workflow starts with a URL that should not be opened merely to satisfy curiosity. The user submits the address, optionally adds HTML already obtained with authorization, selects a model, and reviews both the output and its evidence. MongoDB availability controls dataset-backed pages and prediction-history persistence; the sidebar reports database status.

> [!TIP]
> Treat the evidence panel as a list of measurements to inspect—not as a ranked explanation of intent. Correlation is useful; certainty is a much bigger claim.

```mermaid
%%{init: {'theme':'base','themeVariables': {'primaryColor':'#312E81','primaryTextColor':'#ffffff','primaryBorderColor':'#6D5BD0','lineColor':'#4F46E5','secondaryColor':'#1E3A8A','tertiaryColor':'#111827','background':'#ffffff','mainBkg':'#312E81','nodeBorder':'#6D5BD0','clusterBkg':'#111827','clusterBorder':'#4F46E5'}}}%%
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

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=The+research+workflow+behind+the+model" alt="Offline PhreshPhish data ingestion, feature engineering, machine learning, and artifact export workflow" /></h2>

The model lifecycle is intentionally separate from live analysis. Dataset review and ingestion feed exploration and feature extraction; candidate models are trained and evaluated offline; model artifacts and metadata are then prepared for interactive inference. Bounded samples are useful when validating an experiment. MongoDB must be running for ingestion and database-backed training.

<p align="center"><i>Offline: experiment until the evidence is useful. Online: infer from what was actually saved. No surprise training montage at launch.</i></p>

```mermaid
%%{init: {'theme':'base','themeVariables': {'primaryColor':'#312E81','primaryTextColor':'#ffffff','primaryBorderColor':'#6D5BD0','lineColor':'#4F46E5','secondaryColor':'#1E3A8A','tertiaryColor':'#111827','background':'#ffffff','mainBkg':'#312E81','nodeBorder':'#6D5BD0','clusterBkg':'#111827','clusterBorder':'#4F46E5'}}}%%
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

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=Two+paths%2C+one+consistent+feature+contract" alt="Architecture separating offline ML training from online Streamlit URL analysis" /></h2>

Offline training produces serialized models, metadata, evaluation results, and an artifact inventory. Online inference validates input, invokes the same feature definitions in the training order, loads a saved model, and returns the prediction with observed evidence. It does not fit models during app startup or prediction.

MongoDB stores source records, derived features, model metadata, evaluation summaries, and optional prediction history. It is configured for local or self-hosted use. The exported experiment identifies Random Forest as selected, while the analyzer initially prefers Logistic Regression when available. Choose the model in the interface rather than assuming those defaults are synchronized.

```mermaid
%%{init: {'theme':'base','themeVariables': {'primaryColor':'#312E81','primaryTextColor':'#ffffff','primaryBorderColor':'#6D5BD0','lineColor':'#4F46E5','secondaryColor':'#1E3A8A','tertiaryColor':'#111827','background':'#ffffff','mainBkg':'#312E81','nodeBorder':'#6D5BD0','clusterBkg':'#111827','clusterBorder':'#4F46E5'}}}%%
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

<h2 align="center"><img src="https://readme-typing-svg.demolab.com?font=Manrope&amp;weight=800&amp;size=30&amp;duration=2200&amp;pause=3000&amp;color=6D5BD0&amp;center=true&amp;vCenter=true&amp;width=950&amp;height=62&amp;repeat=false&amp;lines=From+research+bench+to+careful+use" alt="Responsible use of an offline-trained Intelligent URL Threat Analyzer" /></h2>

The application is designed for Python **3.10 or newer**, Streamlit, classical machine-learning estimators, and optional local or self-hosted MongoDB. Model inference requires saved model artifacts. MongoDB enables dataset-backed views, ingestion, and prediction-history persistence. The interface is an analyst-facing view over offline-trained models, not a live protective gateway.

**Use the result as triage, never as authorization to click.** A Benign prediction is not a safety guarantee; a Phishing prediction is not proof of intent. Do not submit data unless you are authorized to handle it. Prediction history may persist in MongoDB. Verify consequential decisions using independent evidence and established security procedures.

<blockquote>
  <b>Best next action:</b> pause, preserve the suspicious message, and use your organization's reporting or incident-response process. Let curiosity investigate; do not let it click.
</blockquote>

<div align="center">
  <img src="https://img.shields.io/badge/%F0%9F%9B%A1%20Decision%20support-Not%20a%20verdict-312E81" alt="Decision support only: predictions are not definitive verdicts" />
  <img src="https://img.shields.io/badge/%F0%9F%8C%90%20Live%20inspection-Not%20performed-111827" alt="The application does not inspect or fetch live websites" />
</div>

<br>

<div align="center">
  <a href="https://huggingface.co/datasets/phreshphish/phreshphish"><img src="https://img.shields.io/badge/%F0%9F%A4%97%20Explore%20the%20data-PhreshPhish-312E81?logo=huggingface&amp;logoColor=white" alt="Explore the PhreshPhish dataset" /></a>
  <a href="https://arxiv.org/abs/2507.10854"><img src="https://img.shields.io/badge/%F0%9F%93%9A%20Read%20the%20research-Paper-1D4ED8" alt="Read the PhreshPhish research paper" /></a>
</div>
