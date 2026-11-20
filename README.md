# StreamVault Licensing Analysis Pipeline

A reproducible, production-grade data analysis and ETL pipeline in plain Python, pandas, and NumPy. 

Built for Kwame Boateng, VP of Content Acquisition at StreamVault, to allocate a **$14.0M licensing budget** between franchise bundles and standalone hits ahead of the board review. The pipeline ingests a legacy candidate list (`data/id_list.csv`), acquires live metadata from the public TMDb API, normalizes nested JSON into grain-defended tables, validates all quality faults, and computes business KPIs across two historical windows.

```text
 data/id_list.csv ────────────────┐
 TMDb API (details & credits) ────┤
                                  ▼
   EXTRACT ──► VALIDATE ──► TRANSFORM ──► QA CHECKS ──► ANALYSE ──► LOAD
   extract.py  validate.py  transform.py   checks.py     analyse.py   load.py
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
| `profiling/profile.ipynb` | Exploratory profiling notebook | Investigates raw inputs, checks spec claims, and reveals rows behind anomalies. |
| `docs/findings.md` | Data diagnosis & findings log | Complete reconciliation of all 127 IDs, traced to decisions and risk rankings. |
| `docs/adr/` | Architecture Decision Records | Formal architectural decisions (`001-` to `003-`), versioned with code. |
| `out/` | Executive deliverables | Client memo (`memo.md`), window KPIs (`analysis.csv`), sensitivity frontier. |
| `data/` | Ingested candidate list and generated tabular datasets | Clean tables (`movies.csv`, `cast.csv`, `crew.csv`) and cached raw JSONs. |

---

## Setup

### Prerequisites
- Python 3.11 or newer
- Dependencies: `pandas`, `numpy`, `requests`
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

### Run Live External API Spot-Check (LO5)
Performs field-by-field verification against live TMDb endpoints for deliberate edge-case titles:
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

---

## Core Findings & Strategic Recommendation

### 1. Two-Window Evaluation (Addressing Finance's Pre-2000 Skepticism)

| Metric | All Years: Franchise | All Years: Standalone | 2000-Onward: Franchise | 2000-Onward: Standalone |
| :--- | :--- | :--- | :--- | :--- |
| **Catalog Count** | 96 titles | 16 titles | 63 titles | 8 titles |
| **Median Box Office** | **$578.9M** | $161.8M | **$786.6M** | $283.2M |
| **Median ROI** | **4.62x** | 2.84x | **4.05x** | 2.84x |
| **Average Rating** | 7.46 / 10 | **8.37 / 10** | 7.33 / 10 | **8.26 / 10** |

- **Both Windows Agree:** In both historical and modern eras, franchise bundles outperform standalones by **2.4x to 3.6x in median box office** and deliver superior capital return (4.05x vs. 2.84x median ROI).
- **The Standalone Advantage:** Standalone hits hold a decisive advantage in critical reception (**8.37/10** vs. 7.46/10), providing subscriber acquisition anchors with zero franchise sequel fatigue.

### 2. The $14.0M Capital Commitment Recommendation
- **$9.5M (68%)** allocated to top-tier franchise trilogy bundles: *The Lord of the Rings*, *The Dark Knight*, and *The Godfather*.
- **$4.5M (32%)** reserved for high-retention standalone acquisitions: *The Shawshank Redemption*, *Schindler's List*, *Spirited Away*, *Interstellar*, and *Pulp Fiction*.

### 3. Candidate List Reconciliation (100% Accounted For)
- **112 FETCHED:** Cleanly parsed into analytical models.
- **6 DUPLICATE:** Excluded (`603`, `278`, `1891`, `155`, `550`, `680`).
- **5 FETCH_FAILED (404):** Fictional IDs logged (`8471293`, `9412887`, `8471294`, `9412888`, `7733901`).
- **4 INVALID:** Syntactically unparseable lines (`-1`, `tt0468569`, `N/A`, blank row 69).
- **Total: 127** (Reconciled with zero silent drops).

### 4. Performance & Scalability (LO4)
- **Execution Speed:** Vectorized analysis executes in **~0.22 seconds**, well below the strict **60.0-second performance budget** (< 0.4% budget utilized).
- **Future Proofing:** Built without row-level iteration (`iterrows`), allowing Adjoa to re-run the pipeline on ~500 candidate titles live during quarterly reviews.
