# ADR 001: Data Grain Definition and Decoupled Tabular Normalization

- **Status:** Accepted
- **Date:** 2026-11-18
- **Context:** Raw responses from the TMDb API arrive as deeply nested JSON trees where a single movie object encapsulates arrays of genre dictionaries, collections, production entities, and hundreds of cast and crew credits. Naive normalization via `pd.json_normalize` on the entire document produces a Cartesian explosion of rows, leading to silent double-counting of box office figures, inflated budgets, and unprovable joins.
- **Decision:** We establish a strict three-table schema with explicitly defended data grains:
  1. `movies`: Exactly one row per unique film (`tmdb_id`). Multi-value scalar properties such as genres are serialized into delimiter-separated strings to protect the primary grain.
  2. `cast`: Exactly one row per film per cast appearance, identified by (`tmdb_id`, `person_id`, `cast_order`).
  3. `crew`: Exactly one row per film per crew assignment, identified by (`tmdb_id`, `person_id`, `department`, `job`).
- **Consequences:** 
  - Prevents Cartesian row inflation during aggregation.
  - Guarantees that summing `revenue` or `budget` across the `movies` table always reflects authentic totals.
  - Requires explicit relational joins when analyzing talent-level impacts.
- **What this survives (Quarterly re-runs on ~500 titles by Adjoa):** This grain architecture scales cleanly as the catalog expands to 500+ titles without running out of memory or altering downstream aggregation logic.
