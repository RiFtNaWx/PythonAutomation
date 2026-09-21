keywords: walk-order, dut-first, channel-first, plus-session, tags, start, buffer, run_prefs
main_idea: Walk order is channel-first (default) or DUT-first, saved in campaign `_manifest/run_prefs.yaml` plus localStorage. + Session is gone; START stamps campaign tags from tags.yaml. BUFFER catalog order stays slew -> settling -> sssr -> lssr -> npr -> power_on_time.

Detail:
- `ate.core.timeline.walk_pairs` drives both the operator timeline and `runner.py`. DUT-first does not reset `prev_dut` on channel change, so CHA->CHB on the same socket skips a re-install prompt.
- UI `#walk-order` next to DUT/channel picks. Change calls `set_run_prefs`. `params()` sends `walk_order` on START.
- `#btn-new-session` removed. `begin_session` copies identity tags/boards/labels into session params when START does not pass them.
- BUFFER yaml/catalog order is the lab sequence. SSSR/LSSR/NPR can still photo-stamp PASS on a flat JPEG -- USB accuracy still needs probes on IN+/VOUT and a live MSO. Do not USB START the whole BUFFER suite until that.
- Check: `python -m ate.core.check_walk_order` (pairs + BUFFER catalog + prefs). Also `check_ui_contract` (no + Session, walk-order present) and `check_tags_datalog` (START stamps tags).
