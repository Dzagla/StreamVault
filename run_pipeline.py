"""
run_pipeline.py
---------------
Single-command, reproducible master execution entry point.
Satisfies the brief requirement:
"Runs top to bottom from a clean clone with no manual edits, and answers both time windows."
Follows multi-stage pipeline architecture:
extract -> transform -> checks -> analyse -> sensitivity
"""

from __future__ import annotations

import time

from pipeline.extract import main as run_extract
from pipeline.transform import flatten_all as run_transform
from pipeline.checks import check_candidate_reconciliation, check_grain_uniqueness
from pipeline.analyse import run_analysis
from pipeline.sensitivity import run_sensitivity


def main() -> None:
    print("=" * 70)
    print("StreamVault Licensing Analysis — Master Pipeline Execution")
    print("=" * 70)

    t0 = time.perf_counter()

    # Stage 1: Extraction & Live API Acquisition
    print("\n>>> STAGE 1: Extraction & Ingestion (pipeline.extract)")
    run_extract()

    # Stage 2: Transformation & Tabular Normalization
    print("\n>>> STAGE 2: Transformation & Tabular Normalization (pipeline.transform)")
    df_movies, df_cast, df_crew = run_transform()

    # Stage 3: Quality Gates & Reconciliation Checks
    print("\n>>> STAGE 3: QA Gates & Reconciliations (pipeline.checks)")
    check_candidate_reconciliation()
    check_grain_uniqueness(df_movies)

    # Stage 4: Analytical Modeling & KPI Generation
    print("\n>>> STAGE 4: Vectorized Analysis Across Windows (pipeline.analyse)")
    run_analysis()

    # Stage 5: Strategic Sensitivity Frontier
    print("\n>>> STAGE 5: Temporal Sensitivity Frontier (pipeline.sensitivity)")
    run_sensitivity()

    total_elapsed = time.perf_counter() - t0
    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETED SUCCESSFULLY in {total_elapsed:.2f} seconds.")
    print("Deliverables generated:")
    print("  • out/analysis.csv           (Two-window KPI table)")
    print("  • out/sensitivity_report.csv (Cutoff sensitivity frontier)")
    print("  • out/memo.md                (Client memo for Kwame Boateng)")
    print("  • docs/findings.md           (Findings log & 127 ID reconciliation)")
    print("  • docs/adr/                  (Architecture Decision Records 001-003)")
    print("  • profiling/profile.ipynb    (Full exploratory data profiling)")
    print("=" * 70)


if __name__ == "__main__":
    main()
