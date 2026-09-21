"""Fail-closed skip rules for daily git pull. Dirty tree must never pull.

Run: python -m ate.core.check_sync_repo
"""
from __future__ import annotations

from pathlib import Path

from ate.core.sync_repo import DAY_S, should_attempt_pull


def main() -> int:
    errors: list[str] = []
    src = Path(__file__).with_name("sync_repo.py").read_text(encoding="utf-8")
    if 'os.environ.get("ATE_APP_ONLY")' not in src:
        errors.append("sync_repo must skip pull when ATE_APP_ONLY is set")
    if '["pull", "--ff-only"]' not in src:
        errors.append("sync_repo must pull --ff-only")
    if should_attempt_pull(True, None, 0.0, False) != "dirty":
        errors.append("uncommitted files must skip pull")
    if should_attempt_pull(True, None, 0.0, True) != "dirty":
        errors.append("--force must still skip pull when dirty")
    if should_attempt_pull(False, 100.0, 100.0 + 60.0, False) != "fresh":
        errors.append("recent stamp must skip pull")
    if should_attempt_pull(False, 100.0, 100.0 + DAY_S + 1.0, False) != "pull":
        errors.append("stale stamp + clean tree must pull")
    if should_attempt_pull(False, 100.0, 100.0 + 60.0, True) != "pull":
        errors.append("--force must ignore the day stamp when clean")
    if should_attempt_pull(False, None, 0.0, False) != "pull":
        errors.append("no stamp + clean tree must pull")
    if errors:
        print("FAIL check_sync_repo:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK check_sync_repo: dirty never pulls, stamp gates, ATE_APP_ONLY skip, ff-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
