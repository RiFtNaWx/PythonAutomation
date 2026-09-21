---
keywords: prd-001, f11, epic-a06, labautomation-1, sssr, lssr, npr, workbook, buffer
main_idea: F11 routes to EPIC-A06 only - thin-wrap LA-1 SSR/LSR/NPR into SSSR/LSSR/NPR workbook use cases. A01-A05 stay closed. Park RS1G/Lim/PowerOn/Noise/PSRR.
---

# 2026-09-03 PRD F11 -> EPIC-A06

PREFLIGHT: PARTIAL. Reuse scale finding + PRD-001. Code check: `ate/tests/opa/stubs.py` still RuntimeError for SSSR/LSSR/NoPhaseReversal.

## Nearness

Artifact: `docs/subagents_findings/2026-09-03_labautomation-1-scale.md` + stubs.py.
A05 made sheet_map honest; BUFFER stubs remain the next buyer-visible gap for "perfect workbook use case."

## Routing

| Item | Decision |
|------|----------|
| F11 | Append ledger -> EPIC-A06 (new) |
| A01-A05 | Stay closed-accepted |
| WIP | A06 only |
| RS1G / Lim / PowerOn / Noise / PSRR | PARKED |
| DataLogger | Keep as pass-fail log; do not replace |
| Next spawn | epic-agent Mode A on A06 only |

## A06 one-liner

Thin-wrap LA-1 SSSR / LSSR / NPR into OpAmp TestSpecs so operator runs write screenshots under Test_Database and paste into the characterization workbook where sheet_map already has anchors.
