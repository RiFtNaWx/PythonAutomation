---
keywords: [demo, sts, vox, step-key, channel, a18, a19, handover]
main_idea: DEMO on RS1G08/RS622/RS2323/RS0204 stamps spec P/F + STS pdf. Empty channel merges as CHA so DEMO/live vos share one latest row.
---

# 2026-09-11 DEMO P/F evidence + channel merge

PREFLIGHT: PARTIAL. Reuse campaign-outline, joinall-vox-fill, a19-a20-a21-handover. Spawn: skip.

Live DEMO 2026-09-11: RS1G08 VOH_4p5V 3.8 PASS, VOL_4p5V 0.55 PASS, ICC 1 PASS; RS622 GBW 7 unspec, VOS 0.7 PASS; RS2323 IPLUS 1 PASS; RS0204 ICC/IL/VOH/VOL PASS. STS `datalog.pdf` + `.md` on each. Fill: VOX G16=3.8, G25=0.55, ICC D10=1, GBW R20=7, Iplus B2=1.

VOX tracking sheet also has 1.65/2.3/3.0 rows. Platform yaml is 2.0/3.3/4.5/5.0/5.5. Map only the 4.5V overlap. Do not alias 1.65 as VOH_2p0V.

`_step_key` now treats missing channel as CHA (same as fill). DEMO vos and live CHA vos are one latest row.
