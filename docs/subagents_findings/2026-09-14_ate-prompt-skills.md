---
keywords: [ate-prompt, skill, ate-add-test, ate-ocr, paddleocr, easyocr, qianfan, unlimited-ocr, ponytail, i-have-adhd, is-it-like-this, path-a, path-b, path-c]
main_idea: Compulsory repo Cursor skills govern ATE prompts. Agent fills a paste block, says Is it like this?, then builds Path A/B/C or OCR-confirm limits. Ponytail and ADHD translated into the clone. Qianfan/Unlimited stay off until named.
---

# 2026-09-14 ATE prompt + OCR skills

PREFLIGHT: HIT. Reuse: PROMPT_GUIDE, VIBE_CODE Path A/B/C, AGENT_PROMPTS section 2, lookup.py, datasheet.py, situations from 116/OVP/catalog/family-PDF findings.

## Shipped

1. `.cursor/skills/ate-prompt/` -- classify, fill block, `Is it like this?`, situations we already met.
2. `.cursor/skills/ate-add-test/` -- Path A/B/C format. Same template as VIBE_CODE.
3. `.cursor/skills/ate-ocr/` -- lookup text first, then PaddleOCR / EasyOCR after affirm. Qianfan-OCR and Unlimited-OCR refuse unless `--i-named-this` and still do not auto-download.
4. `.cursor/skills/ponytail/` and `i-have-adhd/` -- ATE-translated.
5. `.cursor/rules/ate-skills-compulsory.mdc` `alwaysApply: true`.
6. AGENTS / PROMPT_GUIDE / AGENT_PROMPTS / VIBE_CODE / README point at the skills.
7. `check_add_test` fails if ate-prompt / ate-add-test skills vanish.

## OCR loop (not a sidecar)

scrape/extract -> understand family class -> guess specs -> `Is it like this?` -> write `ate/config/limits/<key>.yaml` only. Never `#Test_Database`. Never always-on Unlimited-OCR.

## Proof

```
python -m ate.core.check_add_test
```

Does not prove PaddleOCR is installed. Do not pip install engines until a named OCR job.

## Not done

Qianfan-OCR 5B and Unlimited-OCR are parked on this laptop. Operator zip does not include OCR wheels.
