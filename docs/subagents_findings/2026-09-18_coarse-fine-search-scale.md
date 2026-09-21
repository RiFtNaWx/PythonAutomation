keywords: coarse-to-fine, recipe.search, threshold_search, input_threshold, first_step, N*VCC, schmitt, leftover-honest
main_idea: Path B input_threshold always uses coarse-to-fine (DEFAULT_SEARCH if yaml missing). Formula VIH_min 0.65*VCC and Schmitt VT span scale the first step. Fine-stage interpolate, not the coarse bracket.

Yes we still use coarse then fine. Not a 0..VCC linear walk.

What it does:
- VIH arm 0 walk up. VIL arm VCC walk down. No reverse in a stage.
- First step = largest ladder step <= |limit| (0.5/0.2/0.1/0.05/0.01).
- On hit: skip rest, rearm ~30% back, next smaller step, interpolate last stage.

Scale:
- n=1 buffer (GT34): sweep A.
- n=2 AND (G08): isolation holds other pin (B=H).
- Invert: y_expect invert.
- Schmitt G14: same helper, |limit| = VT+ / VT- span min.
- OE G125: isolation holds OE inactive/active from truth.
- Missing recipe.search: DEFAULT_SEARCH (future SKU does not copy yaml).

Bugs fixed:
- Linear fallback when search yaml missing.
- Formula bands (0.65*VCC) had VIH_min_V=None so first_step collapsed to 0.01.
- Schmitt VT_plus dropped from vcc_grid_owned.
- Interpolate used first coarse crossing and ignored the fine stage.
- Rearm indexed into the global sample list.

Not this job: Ariff TestSpec vih_vil still has its own _search_vin_trip. START Path B id is input_threshold. ICC 0.1 VCC sweep is not this search. check_logic_dc full file still ImportError on seelim resolve_current_tests leftover. check_add_test catalog-order fails are leftover, not this patch.

Proof: python -c _threshold_search_ok PASS. Scale-sim GT34/G08/G14/G125 PASS. Live USB START input_threshold not run this turn (mapping {}).
