---
keywords: [prd-001, ux, setup-clutter, results-first, run-flow, testspec]
main_idea: PRD platform claim (A01-A04) is done. The risk is Setup/Results packing every later epic onto one screen. Operator path stays Apply -> Session -> tick -> START. Import/new-product and ledger/layout are collapsed. Add tests still via TestSpec, not a wizard.
---

# 2026-09-13 PRD vs clean Run

Original PRD: left rail switches real families; START locked until session; add test = `register(TestSpec)` + worker restart; no wizard; A13/A14 parked.

What piled on one page: Setup had campaign + import family + new product + labels + session + START. Results opened with lab board + ledger before the P/F table.

Shipped: Setup `details.setup-more`; Results Last results first; board/ledger/layout in `details.results-more`. No new tab. No new RPC.

Verified in browser: Setup More collapsed; Results table then three collapsed rows; wrap stays on Tests.

Do not: unpark A13/A14, scrape RUN-IC into #Test_Database, put wrap/detect back on Setup, invent Comparator/Power bodies, move START off Setup this pass.

