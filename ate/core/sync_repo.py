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


def main() -> int:
    force = "--force" in sys.argv
    if str(os.environ.get("ATE_APP_ONLY") or "").strip():
        print("SKIP sync_repo: operator app zip (no git pull)")
        return 0
    if not (REPO_ROOT / ".git").is_dir():
        print("SKIP sync_repo: not a git clone")
        return 0

    try:
        dirty = _is_dirty()
    except (OSError, subprocess.TimeoutExpired):
        print("SKIP sync_repo: git status failed")
        return 0

    action = should_attempt_pull(dirty, _read_stamp(), time.time(), force)
    if action == "fresh":
        print("SKIP sync_repo: already fetched today")
        return 0

    try:
        fetch = _git(["fetch", "--all", "--prune"], timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"SKIP sync_repo: fetch failed ({exc})")
        return 0
    if fetch.returncode != 0:
        err = (fetch.stderr or fetch.stdout or "fetch failed").strip().splitlines()
        print("SKIP sync_repo: " + (err[-1] if err else "fetch failed"))
        return 0

    if action == "dirty":
        _stamp_now()
        print("KEEP local files (uncommitted changes). Fetched remotes only. No pull.")
        return 0

    try:
        pull = _git(["pull", "--ff-only"], timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"SKIP sync_repo: pull failed ({exc})")
        return 0
    out = ((pull.stdout or "") + (pull.stderr or "")).strip()
    if pull.returncode != 0:
        print("KEEP local commits. Remote moved too; ff-only refused. Fetch is done.")
        if out:
            print(out.splitlines()[-1][:400])
        return 0
    _stamp_now()
    print(out or "OK sync_repo: already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
