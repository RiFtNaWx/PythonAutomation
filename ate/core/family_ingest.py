"""Ingest an ATE family from GitHub or a local folder (thin plug-in path).

Does not clone the operator's main repo and does not git-init under ate/.
Copies only Python test modules after a fail-closed ATE-family check.
"""
from __future__ import annotations

import ast
import io
import json
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

from ate.core.paths import REPO_ROOT

MYT = timezone(timedelta(hours=8))

TESTS_ROOT = REPO_ROOT / "ate" / "tests"
CONFIG_DIR = REPO_ROOT / "ate" / "config"
EXTRA_FAMILIES_PATH = CONFIG_DIR / "extra_families.yaml"

PROTECTED_FAMILY_KEYS = frozenset({"opamp", "opa", "logic", "level", "lim", "switch"})
PROTECTED_PACKAGE_DIRS = frozenset({"opa", "logic", "level", "lim"})
SKIP_DIR_NAMES = frozenset({
    ".git", ".github", ".venv", "venv", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".mypy_cache",
})
SKIP_FILE_NAMES = frozenset({
    ".env", "env.local", "credentials.json", "secrets.yaml", "id_rsa",
})
_SECRET_NAME_RE = re.compile(
    r"(^|[/\\])(\.env|.*credentials.*|.*secret.*|id_rsa|.*\.pem)$",
    re.I,
)

_FAMILY_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{0,47}$")
_GH_RE = re.compile(
    r"""^
    (?:https?://github\.com/)?
    (?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?
    (?:/(?:tree|blob)/(?P<ref>[^/]+)(?:/(?P<subpath>.*))?)?
    /?\s*$
    """,
    re.VERBOSE | re.I,
)

ATE_PLUGIN_SLOTS = [
    "1. Family package ate/tests/<family>/ with __init__.py that imports modules calling register(TestSpec(...))",
    "2. register(TestSpec) on each test (id, label, required_instruments, fixture_mode, lab_sheet, run)",
    "3. FAMILY_PACKAGES / ate/config/extra_families.yaml mapping \"<family>\": \"ate.tests.<family>\"",
    "4. Optional ate/config/parts/<key>.yaml only if the part needs bench defaults",
    "5. Restart worker (restart_ate_app.bat) if the new family does not appear after ingest",
    "6. Campaign folders under #Test_Database (workbook/, _manifest/sheet_map.yaml)",
    "7. Workbook xlsx via Setup Import xlsx (RPC import_workbook) — not this family ingest",
]

_MAX_PY_BYTES = 1_000_000
_HTTP_TIMEOUT = 30


def _now_tag() -> str:
    return datetime.now(MYT).strftime("%Y%m%d_%H%M%S")


def _plugin_needed(reason: str) -> str:
    slots = "\n".join(f"  - {s}" for s in ATE_PLUGIN_SLOTS)
    return (
        f"{reason}\n"
        "This source is not a drop-in ATE family. Still needed (docs/ATE_PLUGIN.md):\n"
        f"{slots}"
    )


def _looks_like_path(raw: str) -> bool:
    s = (raw or "").strip().strip('"')
    if not s:
        return False
    p = Path(s).expanduser()
    if p.exists():
        return True
    if re.match(r"^[A-Za-z]:[\\/]", s):
        return True
    if s.startswith("\\\\") or s.startswith("./") or s.startswith(".\\"):
        return True
    return False


def parse_github_ref(raw: str) -> dict[str, str]:
    text = (raw or "").strip()
    m = _GH_RE.match(text)
    if not m:
        raise ValueError(
            "Not a GitHub URL or owner/repo (example: https://github.com/org/ate-family "
            "or org/ate-family). Local folders are also accepted."
        )
    repo = m.group("repo")
    if repo.lower().endswith(".git"):
        repo = repo[:-4]
    sub = (m.group("subpath") or "").strip().strip("/")
    return {
        "owner": m.group("owner"),
        "repo": repo,
        "ref": (m.group("ref") or "").strip(),
        "subpath": sub,
    }


def sanitize_family_key(raw: str, *, fallback: str = "") -> str:
    text = (raw or "").strip().lower().replace("-", "_")
    text = re.sub(r"[^a-z0-9_]+", "", text)
    if text.startswith("ate_tests_"):
        text = text[len("ate_tests_"):]
    if text == "opa":
        text = "opamp"
    if _FAMILY_KEY_RE.match(text):
        return text
    fb = re.sub(r"[^a-z0-9_]+", "", (fallback or "").strip().lower().replace("-", "_"))
    if _FAMILY_KEY_RE.match(fb):
        return fb
    raise ValueError(
        "Family key must be a short identifier like analog or comparator "
        f"(got {raw!r}). Do not use opamp/logic/level."
    )


def _is_protected_family(key: str) -> bool:
    return (key or "").strip().lower() in PROTECTED_FAMILY_KEYS


def _backup_dir(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    dest = TESTS_ROOT / "_backup" / f"{path.name}_{_now_tag()}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        shutil.copytree(path, dest)
    else:
        shutil.copy2(path, dest)
    return dest


def _iter_py_files(root: Path) -> list[Path]:
    out: list[Path] = []
    if not root.exists():
        return out
    for p in root.rglob("*.py"):
        if any(part in SKIP_DIR_NAMES for part in p.parts):
            continue
        if p.name in SKIP_FILE_NAMES:
            continue
        if _SECRET_NAME_RE.search(str(p)):
            continue
        out.append(p)
    return out


def _module_looks_like_family(path: Path) -> dict[str, Any]:
    try:
        if path.stat().st_size > _MAX_PY_BYTES:
            return {"ok": False, "reason": "file too large"}
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"ok": False, "reason": str(exc)}
    if _looks_like_full_ate_repo_file(src) and "FAMILY_PACKAGES" in src:
        return {"ok": False, "reason": "core registry, not a family"}
    has_register = bool(re.search(r"\bregister\s*\(", src))
    has_spec = "TestSpec" in src
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "register":
                has_register = True
            if isinstance(node, ast.Name) and node.id == "TestSpec":
                has_spec = True
    except SyntaxError:
        pass
    return {
        "ok": has_register and has_spec,
        "register": has_register,
        "testspec": has_spec,
        "path": str(path),
    }


def _looks_like_full_ate_repo_file(src: str) -> bool:
    return "FAMILY_PACKAGES" in src and "load_family" in src


def _tree_looks_like_main_repo(root: Path) -> bool:
    markers = [
        root / "ate" / "core" / "registry.py",
        root / "ate" / "worker" / "server.py",
        root / "ate" / "tests" / "opa" / "__init__.py",
    ]
    return sum(1 for m in markers if m.is_file()) >= 2


def find_family_root(extracted: Path, subpath: str = "") -> Path:
    base = extracted
    if subpath:
        cand = (extracted / subpath).resolve()
        try:
            cand.relative_to(extracted.resolve())
        except ValueError as exc:
            raise ValueError("Invalid GitHub subpath") from exc
        if cand.exists():
            base = cand
    # zipball wraps a top-level repo-name folder
    kids = [p for p in base.iterdir() if p.is_dir() and p.name not in SKIP_DIR_NAMES] if base.is_dir() else []
    if base.is_dir() and not list(base.glob("*.py")) and len(kids) == 1 and not (base / "ate").exists():
        maybe = kids[0]
        if (maybe / "ate").exists() or list(maybe.rglob("*.py")):
            base = maybe

    if _tree_looks_like_main_repo(base):
        nested = base / "ate" / "tests"
        raise ValueError(
            _plugin_needed(
                "Source looks like a full ATE repo (ate/core + ate/tests), not a single family. "
                "Point at one family folder (local path or GitHub .../tree/<ref>/ate/tests/<family>). "
                f"Nested tests dir: {nested if nested.is_dir() else 'n/a'}."
            )
        )

    hits: list[Path] = []
    scan_root = base if base.is_dir() else base.parent
    for py in _iter_py_files(scan_root):
        info = _module_looks_like_family(py)
        if info.get("ok"):
            hits.append(py)
    if not hits:
        raise ValueError(
            _plugin_needed(
                "No Python module with register(TestSpec) was found in the source."
            )
        )

    # Prefer a directory that already looks like ate.tests.<family>
    for py in hits:
        parent = py.parent
        if parent.name != "__pycache__" and (parent / "__init__.py").is_file():
            if parent.name not in PROTECTED_PACKAGE_DIRS:
                return parent
    return hits[0].parent


def validate_family_dir(family_dir: Path) -> dict[str, Any]:
    hits = []
    for py in _iter_py_files(family_dir):
        info = _module_looks_like_family(py)
        if info.get("ok"):
            hits.append(py.name)
    if not hits:
        raise ValueError(
            _plugin_needed(
                f"{family_dir} has no register(TestSpec) module (thin adapter is OK if it still calls register)."
            )
        )
    return {"modules": hits, "root": str(family_dir)}


def _copy_python_modules(src_dir: Path, dest_dir: Path) -> list[str]:
    copied: list[str] = []
    dest_dir.mkdir(parents=True, exist_ok=True)
    for py in _iter_py_files(src_dir):
        rel = py.relative_to(src_dir)
        if any(part in SKIP_DIR_NAMES or part == "_backup" for part in rel.parts):
            continue
        if _SECRET_NAME_RE.search(str(rel)):
            continue
        if py.stat().st_size > _MAX_PY_BYTES:
            raise ValueError(f"Refusing oversized module {rel} (>{_MAX_PY_BYTES} bytes)")
        dest = dest_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(py, dest)
        copied.append(str(rel).replace("\\", "/"))
    if not copied:
        raise ValueError(_plugin_needed("No Python test modules to copy."))
    init = dest_dir / "__init__.py"
    if not init.is_file():
        mods = [
            Path(c).stem
            for c in copied
            if Path(c).parent == Path(".") and Path(c).stem != "__init__"
        ]
        lines = [
            '"""Imported ATE family — modules call register(TestSpec)."""',
            "",
        ]
        if mods:
            joined = ", ".join(mods)
            lines.append(f"from ate.tests.{dest_dir.name} import {joined}  # noqa: F401")
            lines.append(f"__all__ = {mods!r}")
        else:
            lines.append("__all__: list[str] = []")
        init.write_text("\n".join(lines) + "\n", encoding="utf-8")
        copied.append("__init__.py")
    return copied


def _http_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ATE-family-ingest", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ATE-family-ingest"})
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
        return resp.read()


def _download_github_tree(owner: str, repo: str, ref: str, dest: Path) -> str:
    used_ref = ref
    if not used_ref:
        try:
            meta = _http_json(f"https://api.github.com/repos/{owner}/{repo}")
            used_ref = str(meta.get("default_branch") or "main")
        except Exception:
            used_ref = "main"
    urls = [
        f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{used_ref}",
        f"https://github.com/{owner}/{repo}/archive/refs/heads/{used_ref}.zip",
        f"https://codeload.github.com/{owner}/{repo}/zip/{used_ref}",
    ]
    last_err: Exception | None = None
    data = b""
    for url in urls:
        try:
            data = _download(url)
            if data[:2] == b"PK":
                break
        except urllib.error.HTTPError as exc:
            last_err = exc
            data = b""
            continue
        except Exception as exc:
            last_err = exc
            data = b""
            continue
    if not data:
        raise ValueError(
            f"Could not download GitHub zipball for {owner}/{repo}@{used_ref}: {last_err}"
        )
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if ".." in name.split("/"):
                continue
            zf.extract(info, dest)
    return used_ref


def _record_extra_family(family: str, package: str, source: str) -> Path:
    data: dict[str, Any] = {}
    if EXTRA_FAMILIES_PATH.is_file():
        loaded = yaml.safe_load(EXTRA_FAMILIES_PATH.read_text(encoding="utf-8")) or {}
        if isinstance(loaded, dict):
            data = loaded
    families = data.get("families")
    if not isinstance(families, dict):
        families = {}
        data["families"] = families
    families[family] = {
        "package": package,
        "source": source,
        "imported_at": datetime.now(MYT).isoformat(timespec="seconds"),
    }
    header = (
        "# Extra ATE families (data-driven). Built-ins opamp/logic/level stay in registry.py.\n"
        "# Do not put secrets here. Restart worker if a new family does not appear.\n"
    )
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    EXTRA_FAMILIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXTRA_FAMILIES_PATH.write_text(header + body, encoding="utf-8")
    return EXTRA_FAMILIES_PATH


def _refresh_and_try_load(family: str) -> dict[str, Any]:
    from ate.core import registry as reg

    known = sorted(reg.refresh_family_table())
    return {
        "known": known,
        "loaded_family": None,
        "test_count": None,
        "load_error": None,
        "restart_hint": (
            "If the family rail is stale, run restart_ate_app.bat "
            "(worker :8766, UI :5174; do not touch AirGPT :8765)."
        ),
    }


def import_family(
    *,
    source: str = "",
    family: str = "",
    local_path: str = "",
) -> dict[str, Any]:
    """Copy a GitHub or local ATE family into ate/tests/<family>/."""
    src_raw = str(local_path or source or "").strip().strip('"')
    if not src_raw:
        raise ValueError("Paste a GitHub URL / owner/repo, or a local family folder path.")

    used_local = False
    used_ref = ""
    gh_meta: dict[str, str] | None = None
    tmp: Optional[tempfile.TemporaryDirectory[str]] = None
    try:
        if _looks_like_path(src_raw):
            src_dir = Path(src_raw).expanduser().resolve()
            if not src_dir.exists():
                raise FileNotFoundError(f"Local path not found: {src_dir}")
            if src_dir.is_file():
                if src_dir.suffix.lower() != ".py":
                    raise ValueError("Local file ingest only accepts a .py family module.")
                work = Path(tempfile.mkdtemp(prefix="ate_fam_"))
                shutil.copy2(src_dir, work / src_dir.name)
                family_root = find_family_root(work)
                used_local = True
                source_label = str(src_dir)
            else:
                family_root = find_family_root(src_dir)
                used_local = True
                source_label = str(src_dir)
        else:
            gh_meta = parse_github_ref(src_raw)
            tmp = tempfile.TemporaryDirectory(prefix="ate_gh_")
            extract_to = Path(tmp.name)
            used_ref = _download_github_tree(
                gh_meta["owner"], gh_meta["repo"], gh_meta["ref"], extract_to
            )
            family_root = find_family_root(extract_to, gh_meta.get("subpath") or "")
            source_label = (
                f"https://github.com/{gh_meta['owner']}/{gh_meta['repo']}"
                + (f"/tree/{used_ref}" if used_ref else "")
                + (f"/{gh_meta['subpath']}" if gh_meta.get("subpath") else "")
            )

        fallback = family_root.name if family_root.name not in PROTECTED_PACKAGE_DIRS else ""
        if gh_meta and not fallback:
            fallback = gh_meta["repo"].lower().replace("-", "_")
        key = sanitize_family_key(family, fallback=fallback or "imported")
        if _is_protected_family(key):
            raise ValueError(
                f"Refusing to ingest into protected family {key!r} "
                "(opamp/opa/logic/level). Pick another family key."
            )
        dest = TESTS_ROOT / key
        if dest.name in PROTECTED_PACKAGE_DIRS:
            raise ValueError(f"Refusing to write into protected package {dest}")
        try:
            dest.resolve().relative_to(TESTS_ROOT.resolve())
        except ValueError as exc:
            raise ValueError("Destination escaped ate/tests") from exc

        validate_family_dir(family_root)
        backup = None
        if dest.exists():
            backup = _backup_dir(dest)
            shutil.rmtree(dest)
        copied = _copy_python_modules(family_root, dest)
        validate_family_dir(dest)
        extra = _record_extra_family(key, f"ate.tests.{key}", source_label)
        reload_info = _refresh_and_try_load(key)
        return {
            "ok": True,
            "family": key,
            "package": f"ate.tests.{key}",
            "dest": str(dest),
            "source": source_label,
            "local": used_local,
            "ref": used_ref or None,
            "copied": copied,
            "backup": str(backup) if backup else None,
            "extra_families": str(extra),
            **reload_info,
            "note": (
                f"Family {key} copied into ate/tests/{key}/ and recorded in extra_families.yaml. "
                "Do not import into opamp."
            ),
        }
    finally:
        if tmp is not None:
            tmp.cleanup()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    source = args[0] if args else ""
    fam = args[1] if len(args) > 1 else ""
    result = import_family(source=source, family=fam)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
