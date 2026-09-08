"""Campaign tags: _manifest/tags.yaml SoT + TAGS.txt for grep/Explorer.

Not a new folder axis. Board vocabulary lives in ate/config/boards.yaml.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml

from ate.core.paths import CONFIG_DIR, TEST_DB_ROOT

_TAG_RE = re.compile(r"^[A-Za-z0-9_.:\-/]+$")
BOARDS_PATH = CONFIG_DIR / "boards.yaml"


def _norm_tag(raw: str) -> str:
    t = str(raw or "").strip()
    if not t:
        raise ValueError("empty tag")
    if not _TAG_RE.match(t):
        raise ValueError(f"invalid tag {t!r} (use letters, digits, _.:-/)")
    return t


def tags_yaml_path(ctx) -> Path:
    return ctx.manifest_dir() / "tags.yaml"


def tags_txt_path(ctx) -> Path:
    return ctx.root() / "TAGS.txt"


def load_tags(ctx=None) -> dict[str, Any]:
    from ate.core.database import get_context

    c = ctx or get_context()
    path = tags_yaml_path(c)
    if not path.is_file():
        return {"tags": [], "boards": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {"tags": [], "boards": []}
    tags = [str(x) for x in (data.get("tags") or []) if str(x).strip()]
    boards = [str(x) for x in (data.get("boards") or []) if str(x).strip()]
    return {"tags": tags, "boards": boards}


def save_tags(
    tags: list[str] | None = None,
    boards: list[str] | None = None,
    *,
    ctx=None,
) -> dict[str, Any]:
    """Write tags.yaml + TAGS.txt. Returns saved payload."""
    from ate.core.database import get_context

    c = ctx or get_context()
    c.ensure_tree()
    cur = load_tags(c)
    tag_list = list(tags) if tags is not None else list(cur["tags"])
    board_list = list(boards) if boards is not None else list(cur["boards"])
    seen: set[str] = set()
    clean_tags: list[str] = []
    for t in tag_list:
        n = _norm_tag(t)
        if n.lower() in seen:
            continue
        seen.add(n.lower())
        clean_tags.append(n)
    clean_boards: list[str] = []
    seen_b: set[str] = set()
    for b in board_list:
        n = _norm_tag(b)
        if n.lower() in seen_b:
            continue
        seen_b.add(n.lower())
        clean_boards.append(n)
        board_tok = f"board:{n}"
        if board_tok.lower() not in seen:
            seen.add(board_tok.lower())
            clean_tags.append(board_tok)

    payload = {"tags": clean_tags, "boards": clean_boards}
    ypath = tags_yaml_path(c)
    ypath.parent.mkdir(parents=True, exist_ok=True)
    ypath.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    tpath = tags_txt_path(c)
    lines = list(clean_tags)
    tpath.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return {
        **payload,
        "tags_yaml": str(ypath),
        "tags_txt": str(tpath),
        "root": str(c.root()),
    }


def list_boards(
    *,
    family: str = "",
    package: str = "",
    ctx=None,
) -> list[str]:
    from ate.core.database import family_for_component, get_context

    c = ctx or get_context()
    fam = (family or family_for_component(c.component) or "opamp").strip().lower()
    pkg = (package or c.package or "").strip()
    if not BOARDS_PATH.is_file():
        return []
    data = yaml.safe_load(BOARDS_PATH.read_text(encoding="utf-8")) or {}
    families = (data.get("families") or {}) if isinstance(data, dict) else {}
    fam_block = families.get(fam) or families.get("opamp") or {}
    if not isinstance(fam_block, dict):
        return []
    rows = fam_block.get(pkg) or fam_block.get("default") or []
    return [str(x) for x in rows if str(x).strip()]


def import_tags(from_root: str | Path, *, ctx=None, merge: bool = True) -> dict[str, Any]:
    """Copy tags from another campaign root's tags.yaml into the active campaign."""
    from ate.core.database import get_context

    c = ctx or get_context()
    src = Path(from_root)
    if src.is_dir():
        yml = src / "_manifest" / "tags.yaml"
        if not yml.is_file():
            yml = src / "tags.yaml"
    else:
        yml = src
    if not yml.is_file():
        raise FileNotFoundError(f"No tags.yaml at {from_root}")
    data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("tags.yaml must be a mapping")
    incoming_tags = [str(x) for x in (data.get("tags") or []) if str(x).strip()]
    incoming_boards = [str(x) for x in (data.get("boards") or []) if str(x).strip()]
    if merge:
        cur = load_tags(c)
        incoming_tags = list(cur["tags"]) + incoming_tags
        incoming_boards = list(cur["boards"]) + incoming_boards
    return save_tags(incoming_tags, incoming_boards, ctx=c)


def filter_campaigns_by_tag(
    tag: str,
    *,
    component: str = "",
) -> list[dict[str, Any]]:
    """Scan #Test_Database for campaigns whose TAGS.txt / tags.yaml contain tag."""
    want = str(tag or "").strip().lower()
    if not want:
        return []
    root = TEST_DB_ROOT
    if not root.is_dir():
        return []
    hits: list[dict[str, Any]] = []
    for tags_file in root.rglob("TAGS.txt"):
        try:
            text = tags_file.read_text(encoding="utf-8").lower()
        except OSError:
            continue
        if want not in text:
            continue
        campaign = tags_file.parent
        # Expect .../Component/Part/Package/Operator/Version_N/TAGS.txt
        parts = campaign.parts
        try:
            idx = next(
                i
                for i, x in enumerate(parts)
                if x in ("#Test_Database", "Test_Database")
            )
            comp = parts[idx + 1]
            part = parts[idx + 2]
            package = parts[idx + 3]
            operator = parts[idx + 4]
            version = parts[idx + 5]
        except (StopIteration, IndexError):
            continue
        if component and comp.lower() != component.strip().lower():
            continue
        hits.append(
            {
                "component": comp,
                "part": part,
                "package": package,
                "operator": operator,
                "version": version,
                "root": str(campaign),
                "tags_txt": str(tags_file),
            }
        )
    return hits


def list_tags_rpc(*, ctx=None) -> dict[str, Any]:
    from ate.core.database import get_context

    c = ctx or get_context()
    data = load_tags(c)
    return {
        **data,
        "boards_vocab": list_boards(ctx=c),
        "tags_yaml": str(tags_yaml_path(c)),
        "tags_txt": str(tags_txt_path(c)),
        "root": str(c.root()),
    }
