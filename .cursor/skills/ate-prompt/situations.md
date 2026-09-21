# Situations we already met (ask, confirm, then fix)

Use this when the user's ask matches a trap. State the trap in `Is it like this?`. Do not rediscover.

## Add-test mix

- **Symptom:** "Add a test" as one sentence.
- **Ask:** Path A (this Version catalog), Path B (new TestSpec), or Path C (wrap scaffold)?
- **Confirm:** catalog Save is not a new id. Wrap DEMO with empty `data` is not realization.
- **Fix:** `docs/VIBE_CODE.md` Path A/B/C. Proof `python -m ate.core.check_add_test`.

## runner.py / second stack

- **Symptom:** "hook the new test into START".
- **Ask:** Did they name `runner.py`?
- **Confirm:** they did not. `register(TestSpec)` + `__init__.py` import is enough.
- **Fix:** do not edit `runner.py` / `main.py`.

## input() hangs worker

- **Symptom:** Continue never returns, worker dead.
- **Ask:** is `input()` in `run()`?
- **Confirm:** replace with `params.pause_hook`. START never auto-continues. DEMO SIM may `auto_continue`.

## Web SCPI / Error 116

- **Symptom:** DG822 Pro Undefined Header, "command not in the library".
- **Ask:** did the line come from this repo?
- **Confirm:** golden is `generator_setup.py` only (`APPL SQU/DC`, `OUTP`, `LOAD INF`). Not `:FUNC:SQU:DCYC`, not `:SOUR1:FREQ`, not `:OUTP3`.
- **Fix:** grep this repo. Do not Google SCPI.

## IDD OVP trips

- **Symptom:** DP832 trips at 5.5 V VCC corner.
- **Ask:** is `ovp=5.5` because Vset=OVP or 10% of 5.0?
- **Confirm:** IDD OVP is **5.6 V**. Ceiling still 6.0 V.

## Settle after the whole test

- **Symptom:** CIN/CPD/IDD numbers look like the previous corner.
- **Ask:** sleep after the whole test, or after each VCC/freq/AWG change?
- **Confirm:** `_SETTLE_S` after each change. Log `was` / `d=`.

## Operator All

- **Symptom:** Create folders / DEMO / START disabled or writes the wrong tree.
- **Ask:** operator is a person folder, not All.
- **Confirm:** All is view-only.

## Family PDF class

- **Symptom:** RS2323 limits filled from RS22X opamp PDF.
- **Ask:** filename stem vs inventory class?
- **Confirm:** `RS22X` is RS222/RS224 opamp, not analog switch RS2323. `RS32X` is not LDO RS3213.
- **Fix:** `ate/core/lookup.py` `FAMILY_PARTS`. Double-confirm OCR class.

## Catalog scrape

- **Symptom:** "import all RUN-IC SKUs".
- **Ask:** are we testing this SKU now?
- **Confirm:** one `inventory.yaml` row. Limits yaml only. Never dump PDFs into `#Test_Database`.

## Copy Ariff -> Eugene

- **Symptom:** copy catalog / wrap ids across people or RS0204 dual-rail onto RS1G07.
- **Ask:** same family, this operator Version only?
- **Confirm:** copy-from-part is parked.

## Excel cells guessed

- **Symptom:** FILL_ME, A91, OpAmp golden on Logic.
- **Ask:** did we probe the live xlsx?
- **Confirm:** `sheet_map.yaml` after probe. `campaign_outline.py` for known outlines.

## Leftover SIM + USB

- **Symptom:** START enabled after Open SIM then USB *IDN.
- **Ask:** Discover then Open Session?
- **Confirm:** leftover SIM + USB *IDN refuses START. DEMO with USB *IDN is the live path.

## USB / MSO hang

- **Symptom:** CIN hang, `VI_ERROR_SYSTEM_ERROR`, screenshot poison.
- **Ask:** KEEP USB0, not only SKIP ASRL? Mid-run?
- **Confirm:** idle-restart only. `check_visa`. Do not restart during DUT measure.

## Catalog hid cin/cpd

- **Symptom:** part yaml lists cin, Setup checkbox missing.
- **Ask:** does this Version have a short `test_catalog.yaml`?
- **Confirm:** catalog wins. Tests page Save this Version.

## Wrap scaffold called done

- **Symptom:** `imported_*` DEMO "passes".
- **Ask:** does `run()` return `imported scaffold -- fill body` and no measurements?
- **Confirm:** fill like Path B. Example still-scaffold: `imported_input_off_leakage.py`. Filled: `eugene_cap.py`.

## Noise as nV/rtHz

- **Symptom:** "fix noise to match 11 nV/rtHz".
- **Ask:** 0.1-10 Hz Vpp sheet vs spot density?
- **Confirm:** keep `ate/tests/opa/noise.py`. Do not fake `EN_1kHz`.

## Is-it-like-this then improve

When a guess was wrong:

1. Name which slot was wrong (id, family, cell, engine, OVP).
2. Propose the corrected block.
3. Affirm again only if the write is limits/Excel/OCR/blast-radius.
4. Rebuild the same path. Do not open a second Excel writer or a vector RAG.
