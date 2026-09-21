---
name: ate-prompt
description: >-
  Governs how to specify Cursor prompts for the ATE operator console (ate/ +
  worker 8766 + UI 5174). Use on every ATE task: vibe-code, add a test, add a
  person, datasheet limits, OCR, SCPI, START/DEMO, Excel paste, campaign,
  operator, family, Path A/B/C, debug a failed run, or when the user speaks lab
  English. Fills a prompt block, says "is it like this", waits for affirm on
  guesses, then builds using the repo format. Highest-accuracy prompt skill for
  this repo.
---

# ATE prompt governor (compulsory)

Read this skill before coding. Live product is `ate/` + worker **8766** + UI **5174**.

Companion skills (also auto-use):

- Add / enable / wrap a test -> `.cursor/skills/ate-add-test/SKILL.md`
- Datasheet / PDF / scan / OCR / min-max -> `.cursor/skills/ate-ocr/SKILL.md`
- Writing code -> `.cursor/skills/ponytail/SKILL.md`
- Every reply shape -> `.cursor/skills/i-have-adhd/SKILL.md`

Where: `AGENTS.md`. How: `docs/VIBE_CODE.md`. Paste blocks: [prompt-blocks.md](prompt-blocks.md). Lab traps: [situations.md](situations.md).

## 1. Every ask (do not skip)

1. **Classify** the job (one row). Stop at the first `AGENTS.md` Where-to-change row.
2. **Fill** the matching paste block from [prompt-blocks.md](prompt-blocks.md). Never invent a fourth path.
3. **State** `Is it like this?` plus the filled block (family, part, operator, Path A/B/C, files).
4. **Affirm gate:**
   - User already named Path + family + part + id (or equivalent) -> treat as affirm, build.
   - Guessed cells, OCR numbers, web scrape, blast-radius file, new family, copy-between-people -> **double confirm**, then build.
5. **Build** only those files. Run the matching check. Idle-restart worker if worker-loaded. Ctrl+F5 if UI.
6. **Proof** is DEMO/START of that id, not a green check on an untouched layer.
7. If it fails: cause + which log -> improve the same path. Do not start a second stack.

Restate: `Step N of M done: <what>. Next: <action>.`

## 2. Classify (one row)

| User says | Job | Format skill / file |
|-----------|-----|---------------------|
| Add / enable / wrap a test, new slot, cin, IDD | Add-test Path A/B/C | `ate-add-test` |
| Datasheet, PDF, scan, OCR, min/max, PASS/FAIL | Limits + OCR confirm | `ate-ocr` |
| Turn PSU on, AWG square, DMM, Error 116 | SCPI from this repo | `docs/PROMPT_GUIDE.md` Speak table |
| Add person / operator folder | `owners.yaml` + Setup | prompt-blocks person |
| Testing this SKU | `parts` + one `inventory.yaml` row | prompt-blocks part |
| Excel cell / photo box | Probe live xlsx `sheet_map` | prompt-blocks excel |
| UI tab / button | `ate/ui/web` + `UI_CONTRACT.md` | check_ui_contract |
| Failed START / DEMO | Debug table in VIBE_CODE | sessions logs |
| New family | Import family / extra_families | not `FAMILY_PACKAGES` |

If two jobs appear, finish the first, then ask about the second.

## 3. Highest-accuracy prompt (what you fill)

A prompt is complete only when these slots are named or you asked once:

```
Live: ate/ + 8766 + 5174
Operator: <Name> (not All)
Family: opamp|logic|switch|level|power
Part + package: <RS1G07 SC70-5>
Version: Version_N
Job: Path A | Path B | Path C | person | part | limits/OCR | SCPI | UI | excel | debug
Ids: TestSpec id + measurements[].id
Do not: runner.py / database.py path / input() / web SCPI / catalog scrape / A13
Proof: named check + DEMO that id
```

If a slot is missing and it would pick the wrong files, ask **one** question. If it would only pick a default that AGENTS.md already has, fill the default and say it in `Is it like this?`.

## 4. Confirm language (mandatory shape)

```
Is it like this?
- Job: Path B realize `cin` in family logic for RS1G07
- Files: ate/tests/logic/<id>.py + __init__.py + parts yaml + limits specs id
- Not: runner.py, Path A Save as a new TestSpec, web SCPI
- Proof: python -m ate.core.check_add_test then DEMO cin
Affirm and I build. Or name the slot that is wrong.
```

After affirm: build, check, DEMO. Do not re-ask the same question.

## 5. Auto-use (agents)

Omit nothing because the user spoke casually. Translate lab English through `docs/PROMPT_GUIDE.md` Speak table, then this skill.

Prefix every new ATE chat with the block in `docs/handover/AGENT_PROMPTS.md` section 2 plus:

```
Compulsory skills: .cursor/skills/ate-prompt, ate-add-test, ate-ocr, ponytail, i-have-adhd.
```

## 6. Blast radius (name the file or do not touch)

`ate/core/database.py`, `ate/core/runner.py`, `ate/core/registry.py`, `ate/worker/server.py`, `ate/ui/web/*`.

## 7. Do not

- Mix Path A / B / C in one sentence of work
- Paste web SCPI (Error 116)
- Scrape en.run-ic.com into `#Test_Database`
- Call `input()` in `TestSpec.run`
- Unpark A13. A14 Recipe canvas is live (closed opcodes; no eval)
- Auto-download Qianfan-OCR 5B or start Unlimited-OCR as a sidecar
- Skip `Is it like this?` when the mapping was guessed (OCR, Excel cells, family PDF class)
