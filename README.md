# StreamVault Licensing Analysis Pipeline

A reproducible, modular data analysis and ETL pipeline in plain Python, pandas, and NumPy.

Built for Kwame Boateng, VP of Content Acquisition at StreamVault, to allocate a **$14.0M licensing budget** between franchise bundles and standalone hits ahead of the board review. The pipeline ingests a legacy candidate list (`data/id_list.csv`), acquires live metadata from the public TMDb API, normalizes nested JSON into grain-defended tables, validates all quality faults, and computes business KPIs across two historical windows.

```text
 data/id_list.csv ────────────────┐
 TMDb API (details & credits) ────┤
                                  ▼
   EXTRACT ──► VALIDATE ──► TRANSFORM ──► QA CHECKS ──► ANALYSE ──► SENSITIVITY
   extract.py  validate.py  transform.py   checks.py     analyse.py   sensitivity.py
   └──────────────── run in order, retried, logged, by run_pipeline.py ─────────────────┘
                                  │
                                  ▼
            out/analysis.csv ── out/memo.md ── out/sensitivity_report.csv
```

---

## Architecture & Layout

| Path | What it holds | Why it is separate |
| :--- | :--- | :--- |
| `pipeline/` | Production pipeline code: one file per stage, plus `config.py` | Production logic that runs automatically. No ad-hoc scripts live here. |
| `run_pipeline.py` | Master orchestrator | Single-command runner for an end-to-end, reproducible clean-clone execution. |
| `tests/` | Unit and integration test suite | Proves pipeline logic on hand-made test data before touching production files. |
| `run_tests.py` | Test runner | Runs all 21 unit/integration tests with zero external test runner dependencies. |
| `profiling/profile.ipynb` | Exploratory profiling notebook | Investigates raw inputs, checks spec claims, and reveals rows behind anomalies. |
| `docs/findings.md` | Data diagnosis & findings log | Complete reconciliation of all 127 IDs, traced to decisions and risk rankings. |
| `docs/adr/` | Architecture Decision Records | Formal architectural decisions (`001-` to `003-`), versioned with code. |
| `out/` | Executive deliverables | Client memo (`memo.md`), window KPIs (`analysis.csv`), sensitivity frontier. |
| `data/` | Ingested candidate list and generated tabular datasets | Clean tables (`movies.csv`, `cast.csv`, `crew.csv`); local raw API JSONs in `data/raw/` are excluded via `.gitignore`. |

---

## Setup

### Prerequisites
- Python 3.11 or newer
- Dependencies: `pandas`, `numpy`, `requests`, `pytest` (optional test runner; test suite also executes via standard library `unittest`)
- TMDb API Key (free from [themoviedb.org](https://www.themoviedb.org/settings/api))

### Environment Configuration
Create a `.env` file in the project root (never committed to version control):
```bash
TMDB_API_KEY="your_api_key_here"
```

Verify your setup:
```bash
python check_setup.py
```

---

## Execution

### Run the Complete Pipeline
Executes all stages top-to-bottom from a fresh clone without manual interventions:
```bash
python run_pipeline.py
```

### Run Quality Gates & Live TMDb Spot-Checks
Executes full candidate reconciliation against 127 total rows, multi-table grain uniqueness checks (`movies`, `cast`, `crew`), and live TMDb API spot-checks across edge-case titles:
```bash
python -m pipeline.checks
```

### Run Temporal Sensitivity Frontier
Evaluates the franchise-to-standalone premium multiple across rolling 5-year cutoff thresholds (1985–2010):
```bash
python -m pipeline.sensitivity
```

### Exploratory Data Profiling
Open and run the investigation notebook:
```bash
jupyter lab profiling/profile.ipynb
```

### Run Automated Test Suite
Runs all 21 unit and integration tests covering extraction, validation, transformation, quality gates, and loading:
```bash
python run_tests.py
# or: python -m unittest discover tests
# or: pytest
```

---

## Core Findings & Strategic Recommendation

### 1. Two-Window Evaluation (Addressing Finance's Pre-2000 Skepticism)

| Metric | All Years: Franchise | All Years: Standalone | 2000-Onward: Franchise | 2000-Onward: Standalone |
| :--- | :--- | :--- | :--- | :--- |
| **Catalog Count** | 96 titles | 16 titles | 63 titles | 8 titles |
| **Total Post-2000 Titles** | — | — | **71 titles** (`release_year >= 2000`) |
| **Median Box Office** | **$578.9M** | $161.8M | **$786.6M** | $283.2M |
| **Median ROI** | **4.62x** | 2.84x | **4.05x** | 2.84x |
| **Average Rating** | 7.46 / 10 | **8.37 / 10** | 7.33 / 10 | **8.26 / 10** |

- **Both Windows Agree:** Franchise bundles demonstrate commercial dominance across both horizons: **3.58x median box office superiority across all years** ($578.9M vs. $161.8M) and **2.78x in the 2000-onward window** ($786.6M vs. $283.2M). Across rolling 5-year cutoff thresholds from 1985 to 2000, this premium spans **2.53x to 3.58x** (see `out/sensitivity_report.csv`).
- **The Standalone Advantage:** Standalone hits hold a decisive advantage in critical reception (**8.37/10** vs. 7.46/10 all-years; **8.26/10** vs. 7.33/10 modern), serving as subscriber acquisition and prestige retention anchors with zero sequel fatigue.

### 2. The $14.0M Capital Commitment Recommendation
- **$9.6M (68.6%)** allocated to top-tier franchise trilogy bundles: *The Lord of the Rings* ($4.8M), *The Dark Knight* ($3.3M), and *The Godfather* ($1.5M).
- **$4.4M (31.4%)** reserved for high-retention standalone acquisitions: *Interstellar* ($1.3M), *Spirited Away* ($0.9M), *The Shawshank Redemption* ($0.8M), *Schindler's List* ($0.75M), and *Pulp Fiction* ($0.65M).
- **Total:** Exactly $14.0M capital commitment across 14 curated titles (9 franchise titles, 5 standalone titles).

### 3. Candidate List Reconciliation (100% Accounted For)
- **112 FETCHED:** Cleanly parsed into analytical models.
- **6 DUPLICATE:** Excluded (`603`, `278`, `1891`, `155`, `550`, `680`).
- **5 FETCH_FAILED (404):** Fictional IDs logged (`8471293`, `9412887`, `8471294`, `9412888`, `7733901`).
- **4 INVALID:** Syntactically unparseable lines (`-1`, `tt0468569`, `N/A`, blank row 69).
- **Total: 127** (Reconciled with zero silent drops; FETCHED + DUPLICATE + FETCH_FAILED + INVALID = 127).

### 4. Performance & Scalability (LO4)
- **Execution Speed:** Vectorized analytical KPI calculation (`pipeline.analyse`) executes in **~0.05 seconds**, and the complete master pipeline (`run_pipeline.py`) finishes in **~0.25 seconds** (measured via `time.perf_counter()`), utilizing less than 0.5% of the **60.0-second performance budget**.
- **Future Proofing:** Built strictly using vectorized array operations without row-level iteration (`iterrows`), allowing Adjoa to re-run the pipeline on ~500 candidate titles live during quarterly reviews.
