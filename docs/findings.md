# Findings log

What we found in the data, compared with what the brief and the candidate list specification said, and
where each finding is handled. Evidence is from `profiling/profile.ipynb`. Every finding traces to a decision, the code that applies it, a verification check, and the record of who decided.

## 1. Findings Summary Table

| ID | What we saw | The brief/spec said | Verdict | Decision | Handled in | Proved by | Decided in |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **F1** | 6 rows repeat an earlier TMDb ID (`603`, `278`, `1891`, `155`, `550`, `680`) | "127 film identifiers" (assumed unique) | Defect | Keep the first occurrence; quarantine duplicate rows with reference to first row number | `pipeline/validate.py` | `pipeline/checks.py` | ADR-001 |
| **F2** | Row 69 is an empty blank line in `id_list.csv` | "127 film identifiers" | Defect | Catch during raw line extraction; record as `INVALID (EMPTY_ROW)` to reconcile against 127 | `pipeline/extract.py`, `pipeline/validate.py` | `pipeline/checks.py` | ADR-001 |
| **F3** | Row 93 contains an IMDb ID string (`"tt0468569"`) instead of TMDb integer | "TMDb movie ids, nothing else" | Defect | Reject as `NOT_AN_INTEGER`; verify *The Dark Knight* is already included via ID `155` | `pipeline/validate.py` | `pipeline/checks.py` | ADR-001 |
| **F4** | Row 29 is `-1` and Row 109 is `"N/A"` | Valid positive TMDb IDs | Defect | Reject as `NON_POSITIVE` / `NOT_AN_INTEGER`; quarantine in fetch log | `pipeline/validate.py` | `pipeline/checks.py` | ADR-001 |
| **F5** | 5 IDs (`8471293`, `9412887`, `8471294`, `9412888`, `7733901`) return HTTP 404 Not Found from TMDb API | "Candidate list" | Defect | Retry 3 times with exponential backoff; mark `FETCH_FAILED (404)`; do not crash pipeline | `pipeline/extract.py` | `pipeline/checks.py` | ADR-001 |
| **F6** | Nested JSON schema contains multi-item genre arrays and credits arrays | Tabular candidate data needed | Complex Structure | Unnest into separate grain-defended tables: `movies` (1 row/film), `cast` (1 row/cast appearance), `crew` (1 row/crew role) | `pipeline/transform.py` | `pipeline/checks.py` | ADR-001 |
| **F7** | 41 titles released before 2000 (36.6% of valid titles) | "Yaw in Finance distrusts anything released before 2000" | Structural Split | Compute and report KPIs across both windows (All Years vs 2000-Onward) side by side | `pipeline/transform.py`, `pipeline/analyse.py` | `pipeline/sensitivity.py` | ADR-002 |
| **F8** | High box-office skew in franchise tentpoles (e.g. *Avengers*, *Harry Potter*) | "$14M allocation decision" | Legitimate Asymmetry | Report medians alongside means to protect against single-outlier distortion; compute temporal frontier | `pipeline/transform.py`, `pipeline/analyse.py` | `pipeline/sensitivity.py` | ADR-002, ADR-003 |

---

## 2. Comprehensive Candidate List Reconciliation

The initial evaluation list provided (`data/id_list.csv`) was reviewed, validated, and reconciled. The brief specifies an expected count of 127 identifiers. Our ingestion pipeline accounted for every single candidate without dropping or silently losing records.

### Comprehensive Reconciliation Table

| Status / Category | Count | % of Total | Operational Action Taken |
| :--- | :--- | :--- | :--- |
| **FETCHED (Clean Analyzed Records)** | **112** | **88.2%** | Successfully acquired from TMDb, flattened, and incorporated into analytical models. |
| **DUPLICATE** | **6** | **4.7%** | Identical TMDb IDs present multiple times in CSV. Logged and excluded to prevent double-counting. |
| **FETCH_FAILED (HTTP 404)** | **5** | **3.9%** | Non-existent TMDb IDs in the legacy list. Retried 3 times with exponential backoff before logging. |
| **INVALID Syntax / Type** | **4** | **3.1%** | Syntactically unparseable lines (negative IDs, IMDb format, string N/A, and empty row). |
| **Total Accounts** | **127** | **100.0%** | **Reconciled exactly to the source specification.** |

---

## 3. Granular Breakdown of Source Data Faults

### A. Syntactically Invalid Rows (4 items)
1. **Row 29 (`raw: -1`)** — Negative integer. Invalid ID format in TMDb database.
2. **Row 69 (`raw: ""` / Blank line)** — Empty row in the CSV file that standard readers skip silently.
3. **Row 93 (`raw: "tt0468569"`)** — IMDb ID format instead of TMDb integer identifier (*The Dark Knight*).
4. **Row 109 (`raw: "N/A"`)** — Placeholder string left behind by manual copy-pasting.

### B. Duplicate Candidate Entries (6 items)
Multiple departments submitted overlapping entries over the four-year tracking period:
- **TMDb ID `603`** (*The Matrix*) on Row 42 — duplicate of Row 39.
- **TMDb ID `278`** (*The Shawshank Redemption*) on Row 59 — duplicate of Row 26.
- **TMDb ID `1891`** (*The Empire Strikes Back*) on Row 88 — duplicate of Row 54.
- **TMDb ID `155`** (*The Dark Knight*) on Row 89 — duplicate of Row 1.
- **TMDb ID `550`** (*Fight Club*) on Row 92 — duplicate of Row 78.
- **TMDb ID `680`** (*Pulp Fiction*) on Row 100 — duplicate of Row 7.

### C. Fictional / Erroneous Movie IDs (5 items)
Five IDs resulted in HTTP 404 (Not Found) responses from TMDb:
- **`8471293`** (Row 17)
- **`9412887`** (Row 34)
- **`8471294`** (Row 72)
- **`9412888`** (Row 92)
- **`7733901`** (Row 98)

*Diagnosis:* These 7-digit numeric codes mimic internal legacy catalog numbers or dummy test keys rather than valid TMDb production IDs.

---

## 4. Impact Assessment & Risk Ranking

We ranked each diagnosed fault by its potential impact on the \$14.0M capital allocation decision:

| Risk Rank | Fault Category | Analytical Risk & Impact on Recommendation | Mitigation Applied |
| :--- | :--- | :--- | :--- |
| **1 (Critical)** | **Duplicates** | If unaddressed, duplicate titles like *The Dark Knight* or *The Matrix* would inflate franchise metrics and distort group means/totals. | Tracked first-occurrence row numbers and deduplicated prior to ingestion. |
| **2 (High)** | **Fictional IDs (404s)** | Risk of pipeline termination or unrecorded missing inventory representing missed opportunities. | Implemented robust retry/backoff logic; explicitly logged with proof of non-existence. |
| **3 (Medium)** | **IMDb ID Format** | Missing out on *The Dark Knight* if not converted or already represented. In this specific case, ID `155` was already in the candidate list. | Logged as format fault; verified representation in catalog. |
| **4 (Low)** | **Empty Rows / Strings** | Causes parsing exceptions in naive data loaders. | Strict input cleaning handles nulls safely. |
