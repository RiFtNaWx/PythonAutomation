"""Safe daily git update for vibe-coders. Never overwrites local edits.

Run: python -m ate.core.sync_repo
     python -m ate.core.sync_repo --force   (ignore the 20h stamp; still skip if dirty)

Does not run in the operator zip (no .git / ATE_APP_ONLY).
Never: reset --hard, merge, rebase, stash, checkout --theirs.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from ate.core.paths import REPO_ROOT

STAMP = REPO_ROOT / ".ate_last_sync"
DAY_S = 20 * 3600
_GIT_ENV = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"}


def should_attempt_pull(
    dirty: bool, last: float | None, now: float, force: bool
) -> str:
    """dirty | fresh | pull -- dirty always wins so local files stay."""
    if dirty:
        return "dirty"
    if not force and last is not None and (now - last) < DAY_S:
        return "fresh"
    return "pull"


def _git(args: list[str], timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
        env=_GIT_ENV,
    )


def _stamp_now() -> None:
    try:
        STAMP.write_text(str(int(time.time())), encoding="utf-8")
    except OSError:
        pass


def _read_stamp() -> float | None:
    try:
        return float(STAMP.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _is_dirty() -> bool:
    r = _git(["status", "--porcelain"])
    return bool((r.stdout or "").strip())


def run_sync(*, force: bool = False) -> dict:
    """Fetch + ff-only pull. Never overwrites a dirty tree. Safe for UI splash."""
    if str(os.environ.get("ATE_APP_ONLY") or "").strip():
        return {"action": "skip", "message": "App package -- software updates come with a new zip."}
    if not (REPO_ROOT / ".git").is_dir():
        return {"action": "skip", "message": "Not a git clone."}

    try:
        dirty = _is_dirty()
    except (OSError, subprocess.TimeoutExpired):
        return {"action": "skip", "message": "Could not read git status."}

    action = should_attempt_pull(dirty, _read_stamp(), time.time(), force)
    if action == "fresh":
        return {"action": "fresh", "message": "Already updated today."}

    try:
        fetch = _git(["fetch", "--all", "--prune"], timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"action": "skip", "message": f"Update check failed ({exc})."}
    if fetch.returncode != 0:
        err = (fetch.stderr or fetch.stdout or "fetch failed").strip().splitlines()
        return {"action": "skip", "message": err[-1] if err else "Update check failed."}

    if action == "dirty":
        _stamp_now()
        return {
            "action": "dirty",
            "message": "Your local edits were kept. Fetched remotes only.",
        }

    try:
        pull = _git(["pull", "--ff-only"], timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"action": "skip", "message": f"Pull failed ({exc})."}
    out = ((pull.stdout or "") + (pull.stderr or "")).strip()
    if pull.returncode != 0:
        return {
            "action": "diverged",
            "message": "Your local commits were kept. Fetch is done.",
        }
    _stamp_now()
    msg = out.splitlines()[-1][:200] if out else "Already up to date."
    if "Already up to date" in out or "already up to date" in out.lower():
        return {"action": "fresh", "message": "Already up to date."}
    return {"action": "pull", "message": msg or "Updated."}


def main() -> int:
    force = "--force" in sys.argv
    result = run_sync(force=force)
    print(result.get("message") or result.get("action") or "OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
