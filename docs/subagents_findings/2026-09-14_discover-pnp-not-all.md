keywords: discover, visa, pnp, ghost, awg, psu, mso, classify_idn, visa_known, tiles
main_idea: Discover must not treat every visa_known.yaml AWG/PSU/MSO URL as live. Only Windows PnP Status=OK serials that answer *IDN light tiles. Ghost USBTMC and USB serial strings (DG8Q...) are not instruments.

## Bug

`visa_known.yaml` lists one URL per kind. Discover *IDN'd all of them when PnP returned empty (fail-open), and `classify_idn` used `"DG8" in u` so a USB serial `DG8Q281600755` classified as AWG without a real IDN. Open Session force-rescanned whenever MSO was missing (12s hang). UI required MSO+PSU+AWG even for Logic PSU/DMM. Empty Discover restored SIM tiles so all four looked detected.

Earlier today AWG/DMM were PnP Unknown and MSO timed out. After this fix, `check_visa` *IDN'd PSU+AWG+DMM+MSO on the yaml serials (keep=those four, skip=[]). Ghosts still drop when PnP OK is empty or the serial is Unknown.

## Fix

- `probe_visa_urls`: empty PnP OK -> probe nothing; yaml ghost serials dropped; live extra PnP serials allowed
- `classify_idn` uses the IDN model field; VISA URLs return None
- `visa_inventory.keep` = *IDN mapping only; skip = yaml that did not *IDN
- Open Session rescans only when mapping is empty
- Tiles stay off on empty Discover even if SIM is open

## Checks

- `python -m ate.core.check_visa`
- `python -m ate.core.check_ui_contract`
- `python -m ate.core.check_mapped_tests`

Does not prove a live AWG/MSO *IDN on this bench.

## Do not

- `list_resources()` on this PC
- Claim AWG/MSO detected from yaml presence
- Restore SIM tiles after a USB Discover miss
