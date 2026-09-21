keywords: start, ioz, btn-start, applyDb, loadTests, runPollActive, waitForRunComplete, DELAY, WAIT, Continue, sessionOpen, notice, leftover-honest
main_idea: START is not a silent no-op when the click fires. Dead look is (1) disabled #btn-start with no session, (2) applyDb/loadTests wiping Setup ticks, (3) WAIT/DELAY mistaken for a new START. Right-side dock still clicks.

PREFLIGHT: HIT. Reuse app.js START/applyDb/waitForRunComplete + index.html chrome + 2026-09-21_rs1g126-ioz-usb-awg.md (boot splash hang) + 2026-09-21_ui-click-demo-proof.md (USB START needs Continue).

## 1. Worker busy / Continue WAIT -- START click is not silent

Handler is `clickStartOrContinue` (`ate/ui/web/app.js:5872`), bound on `#btn-start` (`5857`) and `#run-dock-go` (`6118`).

| State | What START does | Notice? |
|-------|-----------------|---------|
| `pendingPrompt` (WAIT Continue, even if modal dismissed / `gateHeld`) | `switchPage("run")` then `respondContinue()` (`5873-5880`). Does **not** start a new sequence. | Only on Continue RPC error |
| `runPollActive` and worker `busy` (DELAY settle or still running) | `switchPage("run")`, notice, return (`5882-5889`) | **Yes:** `Run already in progress -- Continue is on the right, or Abort. DELAY is settle, not a dead START.` |
| `runPollActive` but worker idle | Clears the stale flag (`5891`) and continues into a new START | No |
| Second guard in `startInstrumentRun` | `if (runPollActive) return notice("Run already in progress")` (`5935-5943`) | **Yes** |

`applyDb` while busy also notices `Run in progress -- campaign locked...` (`3499-3502`) and returns without throwing. START only calls `applyDb` when campaign fields changed (`5906-5911`), so a WAIT re-click usually never hits that path.

Not a silent return. The look-dead case is: operator wanted a **new** IOZ START, but WAIT made the same button **Continue** (dock label `Continue` at `paintRunDock` `1570-1572`). Leaving Run while WAIT calls `dismissOperatorModal` (`switchPage` `710-711`) so the modal is gone; Setup START still Continues.

## 2. applyDb before run_sequence_async -- delay + tick wipe

Current START does **not** always await `applyDb`. `ids = selectedTests()` first (`5896`), then `applyDb` only if `!campaignAlreadyApplied()` (`5859-5911`). After that, `await startInstrumentRun(ids)` which `await rpc("run_sequence_async")` (`5966`).

If campaign **is** already applied (normal after Setup Apply + tick IOZ): no `applyDb`, `startInstrumentRun` hits `switchPage("run")` at `5944` almost immediately. Short dead window only if `session_status` / `bench_preflight` hangs (`5913-5928`) **before** the Run tab switch.

If campaign **changed**: `await applyDb()` before Run tab. `applyDb` chains `set_db_context` + `loadOwners` + `loadParamDefaults` + `loadFixtureCatalog` + **`loadTests`** + coverage/detect/catalog/tags (`3525-3568`). That can look like a dead click (no RUN strip yet). `applyDb` catch is empty (`5909-5910`) -- apply failure is silent, then START still proceeds with captured `ids`.

`loadTests` (`4151`) rebuilds `#test-list` from `list_tests`. `preferred` is always empty (`4171`). Checkboxes are unchecked unless `preferred.has(t.id)` (`4201`). **Every `loadTests` unchecks IOZ on Setup.** Captured `ids` still go to `run_sequence_async`, so the run can start while the tick visually vanishes. If `loadTests` ran **before** the click (Apply, family switch, Save catalog, boot), `selectedTests()` is empty -> notice `Select at least one test` (`5897`). Tests-page `#campaign-tests` ticks are **not** `selectedTests()` (`1193` vs `campaignTestOrderIds` `3705`).

## 3. #btn-start disabled without session -- click never fires

`index.html:321`: `<button id="btn-start" ... disabled>`. `refreshSession` sets `$("btn-start").disabled = !sessionOpen` (`4655`). Native disabled button: **no onclick**, so `clickStartOrContinue` never runs and **no notice**. Open Session / Open SIM / DEMO set `disabled = false` (`5400`, `5432`, `5848`). Handler still notices `Open Session or Open SIM first` (`5900`, `5934`) if invoked while `sessionOpen` is false.

`#run-dock-go` (`index.html:88`) is **never disabled**. Same handler. Right-side START still notices when Setup START is grey.

`#boot-splash` (`index.html:14`, z-index 5000) blocks all clicks until `hideBootSplash` (`7434`). If `loadTests`/`refreshSession` hang, splash stays on Loading (already seen in `2026-09-21_rs1g126-ioz-usb-awg.md`).

## 4. waitForRunComplete does not leave runPollActive true on a normal exit

`startInstrumentRun` sets `runPollActive = true` (`5960`) then `await waitForRunComplete` (`5967`). `finally` always sets `runPollActive = false` (`6015-6017`). `waitForRunComplete` (`6020-6042`) loops 14400 x 250 ms (~1 h), returns when `run_epoch` advanced and `!busy`, or throws idle-10 (`Worker restarted...`) or timeout. Throws go to catch + **still** `finally`.

Stuck `true` only if:
- `session_status` RPC never returns (loop never exits, `finally` not reached)
- boot reconnect (`7422-7428`) sets `runPollActive` then `waitForRunComplete().then(paintSessionReport).then(clear)` -- if `paintSessionReport` hangs after a finished wait, flag stays until next START sees `!busy` and clears it (`5882-5891`)

STOP sets `runPollActive = false` immediately (`6049`) while `waitForRunComplete` may still be looping.

## 5. DELAY settle vs WAIT Continue

`parseDelayS` (`1488-1493`): progress text must match `settle|dwell|delay` **and** `N s`. Then `noteActivity` phase `delay` (`1501-1502`). Strip phase **DELAY** (`1554-1555`). Dock label **DELAY** (`1573-1574`). Continue buttons stay **hidden** unless `pendingPrompt` (`1536-1538`). `tick()` refreshes the countdown (`6996-6998`). `#next-banner` on Run tab: `DELAY: ... (Ns left)` (`1821-1823`).

WAIT is `waiting_operator` / `pendingPrompt`: strip **WAIT**, dock **Continue**, banner `WAIT: ... blocked until Continue or Abort` (`1815-1820`). USB START always needs operator Continue (`2026-09-21_ui-click-demo-proof.md`). IOZ `settle_s` 0.3 is short; board/DUT Continue is the long pause. DELAY with no Continue can be mistaken for a dead UI if the operator stays on Setup and ignores `#run-strip` / right dock.

## Leftover-honest

- Did not run UI, worker, or DEMO. Read-only.
- `preferred` never populated -- Setup ticks never persist across `loadTests`.
- Disabled Setup START is the only true no-handler click.
- INDEX.md not updated (parent asked skip).
