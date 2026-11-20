"""
run_pipeline.py
---------------
Single-command, reproducible master execution entry point.
Satisfies the brief requirement:
"Runs top to bottom from a clean clone with no manual edits, and answers both time windows."

Follows multi-stage pipeline architecture:
extract -> validate -> transform -> checks -> analyse -> sensitivity
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from pipeline.config import (
    ID_LIST,
    OUT_DIR,
    ANALYSIS_OUT,
    SENSITIVITY_OUT,
    MEMO_OUT,
    ensure_directories,
)
from pipeline.validate import validate_candidates
from pipeline.extract import main as run_extract
from pipeline.transform import flatten_all as run_transform
from pipeline.checks import (
    check_candidate_reconciliation,
    check_grain_uniqueness,
    ReconciliationError,
)
from pipeline.analyse import run_analysis
from pipeline.sensitivity import run_sensitivity


def _report_partial_state(failed_stage: str, error: Exception) -> None:
    """Report failure stage and current state of output artifacts for catalog team."""
    print("\n" + "!" * 70)
    print(f"PIPELINE RUN FAILED AT STAGE: {failed_stage}")
    print(f"Exception: {type(error).__name__}: {error}")
    print("!" * 70)

    print("\nCurrent State of Deliverables (`out/` directory):")
    expected_outputs = [
        ("out/analysis.csv", ANALYSIS_OUT),
        ("out/sensitivity_report.csv", SENSITIVITY_OUT),
        ("out/memo.md", MEMO_OUT),
    ]
    for label, path in expected_outputs:
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"  [PARTIAL/PREVIOUS] {label} exists ({size_kb:.1f} KB)")
        else:
            print(f"  [NOT GENERATED]    {label} does not exist")
    print("\nNote: Please resolve the QA failure above before deploying outputs.")
    print("!" * 70 + "\n")


def main() -> None:
    print("=" * 70)
    print("StreamVault Licensing Analysis — Master Pipeline Execution")
    print("=" * 70)

    ensure_directories()
    t0 = time.perf_counter()
    current_stage = "Initialization"

    try:
        # Stage 1: Extraction & Ingestion
        current_stage = "Stage 1: Extraction (pipeline.extract)"
        print(f"\n>>> {current_stage}")
        run_extract()

        # Stage 2: Validation of Candidate Pool
        current_stage = "Stage 2: Validation (pipeline.validate)"
        print(f"\n>>> {current_stage}")
        records = validate_candidates(ID_LIST)
        invalid_count = sum(1 for r in records if r["disposition"] == "INVALID")
        dup_count = sum(1 for r in records if r["disposition"] == "DUPLICATE")
        print(f"  ✓ Validated {len(records)} candidate rows from {ID_LIST.name}")
        print(f"  ✓ Quarantine breakdown: {invalid_count} syntax errors, {dup_count} duplicate candidate rows")

        # Stage 3: Transformation & Tabular Normalization
        current_stage = "Stage 3: Transformation & Normalization (pipeline.transform)"
        print(f"\n>>> {current_stage}")
        df_movies, df_cast, df_crew = run_transform()

        # Stage 4: Quality Gates & Reconciliation Checks
        current_stage = "Stage 4: QA Gates & Reconciliations (pipeline.checks)"
        print(f"\n>>> {current_stage}")
        check_candidate_reconciliation()
        check_grain_uniqueness(df_movies)

        # Stage 5: Vectorized Analysis Across Windows
        current_stage = "Stage 5: Vectorized Analysis Across Windows (pipeline.analyse)"
        print(f"\n>>> {current_stage}")
        run_analysis()

        # Stage 6: Strategic Sensitivity Frontier
        current_stage = "Stage 6: Temporal Sensitivity Frontier (pipeline.sensitivity)"
        print(f"\n>>> {current_stage}")
        run_sensitivity()

    except (ReconciliationError, AssertionError, Exception) as exc:
        _report_partial_state(current_stage, exc)
        sys.exit(1)

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
