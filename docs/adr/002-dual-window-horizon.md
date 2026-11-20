# ADR 002: Dual-Window Horizon (All-Years vs. 2000-Onward)

- **Status:** Accepted
- **Date:** 2026-11-18
- **Context:** Yaw in Finance distrusts metrics from pre-2000 films due to historical inflation, currency exchange variances, and shifts in international box office accounting. There is an organizational risk that a single blended metric will be rejected in the board room.
- **Decision:** We execute and present all critical KPI evaluations across two independent analytical windows:
  1. Window A: All historical titles (112 titles total: 96 franchise, 16 standalone).
  2. Window B: Post-2000 titles (filter: `release_year >= 2000`, exactly 71 titles total: 63 franchise and 8 standalone).
- **Consequences:**
  - Demonstrates whether the strategic superiority of franchise bundles is robust or an artifact of vintage eras. Both windows confirm franchise commercial dominance: 3.58x median box office superiority across all years ($578.9M vs. $161.8M) and 2.78x in the post-2000 window ($786.6M vs. $283.2M).
  - Defuses potential methodological objections from Finance prior to executive deliberation.
- **What this survives:** As Adjoa adds future quarters of titles, the post-2000 subset will naturally comprise an increasing proportion of the catalog, ensuring longitudinal consistency.
