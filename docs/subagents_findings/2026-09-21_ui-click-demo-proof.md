---
keywords: ui, click, DEMO, Apply, Open SIM, test_params, settle_s, leftover-honest
main_idea: Proof is operator console clicks, not extra Python helpers. Eugene + Apply RS1GT34 + tick input_threshold + Write settle_s 0.3 + Open SIM + DEMO. test_params.yaml on disk. USB START still needs Continue.
---

PREFLIGHT: HIT. Reuse UI_CONTRACT DEMO/Open SIM, Path A Write.

## Clicks (http://127.0.0.1:5174)

1. Operator header -> Eugene
2. Setup Apply campaign Logic / RS1GT34 / SOT23-5 / Eugene / Version_1
3. Tick `input_threshold`, set Settle 0.3 s, Write
4. Open SIM (fake PyVISA: PSU+AWG+DMM+MSO)
5. DEMO (SIM) -- campaign locked Logic/RS1GT34; config_change ran

## Disk proof

`#Test_Database/Logic/RS1GT34/SOT23-5/Eugene/Version_1/_manifest/test_params.yaml`

```
tests.input_threshold.settle_s: 0.3
vcc_start: 2.0  vcc_stop: 5.5  vcc_step: 0.1
```

That file is Path A Parameters Write, not a new TestSpec.

## Leftover-honest

- Did not add a new TestSpec or extra RPC helper for this proof.
- All-families walker also owns 8766 and switched SKUs (AnalogSwitch / RS2G08) after DEMO. Session JSON names can land under the last Apply folder.
- USB START still needs operator Continue. SIM DEMO is not Verify PASS.
- Tests Path A list showed OpAmp ids until Apply campaign on Setup.
