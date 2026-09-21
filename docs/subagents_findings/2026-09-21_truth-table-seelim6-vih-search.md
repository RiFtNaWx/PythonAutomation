keywords: truth-table, seelim-6, delta_icc, 2^n, DEFAULT_SEARCH, coarse-fine, vih, isolation, leftover-honest
main_idea: SeeLim-6 is the dICC subset (6 all-H/all-L bookends of 12). Path B now always walks n*2^(n-1) via delta_icc_vectors, fail-closes incomplete combinational 2^n tables, and VIH always uses DEFAULT_SEARCH coarse-to-fine (no 0..VCC linear walk). Isolation_for_run stays one track-or-invert per pin so VIH stays cheap.

PREFLIGHT: HIT. Reuse 2026-09-21_rs1g97-dicc-12seq.md, 2026-09-18_coarse-fine-search-scale.md. spawn skip.

What changed:
- `delta_icc_vectors` for every n (n=1 is 1 vector, not 2 duplicate others_high).
- `missing_truth_vectors` + `check_logic_dc._all_truth_coverage_ok` on every Path B combinational SKU.
- `_sweep_threshold` always `effective_search` + `edge_limit` (Schmitt VT+ lo, else VIH_min/VIL_max). Missing yaml search is DEFAULT_SEARCH.
- XOR dual isolation stays on the table; run still prefers first track (efficient VIH).

leftover-honest:
- `python -m ate.core.check_logic_dc` did not return this turn (shell/python wrapper wedged). Proof is the new FAIL bars in check_logic_dc, not a green SIM walk.
- `ate/core/check_logic_dc_sim.py` is still missing (pre-existing import at end of check_logic_dc).
- RS1G97 has no vcc_grid blob; Schmitt VT first_step falls back to finest ladder until a signed grid exists.
- Ariff `vih_vil` still has `_search_vin_trip`. Path B id is `input_threshold`.
- Live USB START not run this turn.
