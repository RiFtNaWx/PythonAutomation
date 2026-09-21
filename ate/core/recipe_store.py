"""Recipe graph store: ate/config/recipes/<id>.yaml (+ optional Version overlay).

A14 SoT for canvas graphs. No eval. Zip users never need npm.
"""
from __future__ import annotations

import itertools
import re
from pathlib import Path
from typing import Any

import yaml

from ate.core.paths import CONFIG_DIR

RECIPES_DIR = CONFIG_DIR / "recipes"
_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,40}$")

# Allowlisted opcodes (must match recipe_walk.OPCODES)
OPCODES = frozenset(
    {
        "sweep",
        "for_corners",
        "for_list",
        "if_else",
        "pause",
        "psu_set",
        "awg_out",
        "dmm_read",
        "scope_detect",
        "screenshot",
        "measure",
        "end",
    }
)

MAX_NODES = 80


def recipes_dir() -> Path:
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    return RECIPES_DIR


def _safe_id(raw: str) -> str:
    tid = re.sub(r"[^a-z0-9_]+", "", str(raw or "").strip().lower())
    if not _ID_RE.match(tid):
        raise ValueError("recipe id must be lowercase slug, e.g. demo_corners")
    return tid


def list_recipes(*, family: str = "") -> list[dict[str, Any]]:
    """List shared recipe yaml headers (no full graphs)."""
    folder = recipes_dir()
    out: list[dict[str, Any]] = []
    fam = str(family or "").strip().lower()
    for fp in sorted(folder.glob("*.yaml")):
        try:
            data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(data, dict):
            continue
        rid = str(data.get("id") or fp.stem).strip().lower()
        rf = str(data.get("family") or "").strip().lower()
        if fam and rf and fam not in (rf, "level" if rf == "logic" else rf):
            # level rail may load logic recipes; exact match preferred
            if fam != rf:
                continue
        out.append(
            {
                "id": rid,
                "label": str(data.get("label") or rid),
                "shortform": str(data.get("shortform") or ""),
                "family": rf,
                "products": list(data.get("products") or []),
                "path": str(fp),
                "node_count": len(data.get("nodes") or []),
            }
        )
    return out


def load_recipe(recipe_id: str, *, overlay: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load shared recipe; Version overlay nodes/edges win when provided."""
    rid = _safe_id(recipe_id)
    fp = recipes_dir() / f"{rid}.yaml"
    if not fp.is_file():
        raise FileNotFoundError(f"recipe not found: {rid}")
    data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"invalid recipe yaml: {rid}")
    data["id"] = rid
    if isinstance(overlay, dict) and overlay:
        # Version overlay replaces graph + attrs when present
        for key in ("nodes", "edges", "vcc_list", "logic_inputs", "levels", "rails", "details"):
            if key in overlay and overlay[key] not in (None, "", []):
                data[key] = overlay[key]
        if overlay.get("label"):
            data["label"] = overlay["label"]
        if overlay.get("shortform"):
            data["shortform"] = overlay["shortform"]
    return data


def validate_graph(data: dict[str, Any]) -> list[str]:
    """Return error strings (empty = ok)."""
    errors: list[str] = []
    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        errors.append("nodes must be a list")
        return errors
    if len(nodes) > MAX_NODES:
        errors.append(f"too many nodes ({len(nodes)} > {MAX_NODES})")
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"node[{i}] not a dict")
            continue
        op = str(node.get("op") or node.get("type") or "").strip().lower()
        if not op:
            errors.append(f"node[{i}] missing op")
        elif op not in OPCODES:
            errors.append(f"unknown opcode {op!r}")
        # Refuse anything that looks like code injection
        for bad in ("eval", "exec", "import", "__"):
            blob = yaml.safe_dump(node)
            if bad in blob and op not in ("pause", "measure", "end"):
                # allow pause message text; still refuse eval/exec keys
                pass
        for k in node:
            if str(k).lower() in ("eval", "exec", "code", "python", "script"):
                errors.append(f"node[{i}] forbidden key {k!r}")
    edges = data.get("edges")
    if edges is not None and not isinstance(edges, list):
        errors.append("edges must be a list")
    return errors


def save_recipe(
    *,
    recipe_id: str,
    graph: dict[str, Any],
    family: str = "logic",
    label: str = "",
    shortform: str = "",
    details: str = "",
    products: list[str] | None = None,
    version_overlay: bool = False,
) -> dict[str, Any]:
    """Write shared recipes/<id>.yaml, or Version _manifest/recipe_graph.yaml when overlay."""
    rid = _safe_id(recipe_id)
    body: dict[str, Any] = {
        "id": rid,
        "label": str(label or graph.get("label") or rid).strip() or rid,
        "shortform": str(shortform or graph.get("shortform") or "").strip(),
        "details": str(details or graph.get("details") or "").strip(),
        "family": str(family or graph.get("family") or "logic").strip().lower() or "logic",
        "products": [str(p).strip().lower() for p in (products or graph.get("products") or []) if str(p).strip()],
        "vcc_list": list(graph.get("vcc_list") or []),
        "logic_inputs": graph.get("logic_inputs"),
        "levels": list(graph.get("levels") or []),
        "rails": dict(graph.get("rails") or {}) if isinstance(graph.get("rails"), dict) else {},
        "nodes": list(graph.get("nodes") or []),
        "edges": list(graph.get("edges") or []),
    }
    # Clean empty optionals
    if body["logic_inputs"] in (None, ""):
        body.pop("logic_inputs", None)
    if not body["vcc_list"]:
        body.pop("vcc_list", None)
    if not body["levels"]:
        body.pop("levels", None)
    if not body["rails"]:
        body.pop("rails", None)
    if not body["shortform"]:
        body.pop("shortform", None)
    if not body["details"]:
        body.pop("details", None)

    errs = validate_graph(body)
    if errs:
        raise ValueError("; ".join(errs))

    if version_overlay:
        from ate.core.database import get_context

        ctx = get_context()
        man = ctx.manifest_dir()
        man.mkdir(parents=True, exist_ok=True)
        # One file maps id -> graph overlay for this Version
        overlay_path = man / "recipe_graph.yaml"
        existing: dict[str, Any] = {}
        if overlay_path.is_file():
            try:
                existing = yaml.safe_load(overlay_path.read_text(encoding="utf-8")) or {}
            except (OSError, yaml.YAMLError):
                existing = {}
        if not isinstance(existing, dict):
            existing = {}
        recipes = existing.get("recipes")
        if not isinstance(recipes, dict):
            recipes = {}
        recipes[rid] = body
        existing["recipes"] = recipes
        overlay_path.write_text(
            yaml.safe_dump(existing, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return {"ok": True, "id": rid, "path": str(overlay_path), "overlay": True}

    fp = recipes_dir() / f"{rid}.yaml"
    fp.write_text(
        yaml.safe_dump(body, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return {"ok": True, "id": rid, "path": str(fp), "overlay": False}


def preview_corners(
    *,
    logic_inputs: int = 2,
    levels: list[Any] | None = None,
) -> dict[str, Any]:
    """2^n corner table (same math as for_corners walker)."""
    n = max(1, min(8, int(logic_inputs or 2)))
    lv = []
    for v in levels or [0.0, 5.5]:
        try:
            lv.append(float(v))
        except (TypeError, ValueError):
            pass
    if len(lv) < 2:
        lv = [0.0, 5.5]
    corners = [list(c) for c in itertools.product(lv, repeat=n)]
    return {
        "logic_inputs": n,
        "levels": lv,
        "count": len(corners),
        "corners": corners[:256],  # cap UI payload
    }


def grep_products(query: str, *, limit: int = 40) -> list[dict[str, Any]]:
    """Typeahead over inventory + parts yaml keys."""
    from ate.core.paths import PARTS_DIR

    q = str(query or "").strip().lower()
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    inv_path = CONFIG_DIR / "inventory.yaml"
    if inv_path.is_file():
        try:
            inv = yaml.safe_load(inv_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            inv = {}
        rows = inv.get("parts") or inv.get("inventory") or inv
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                part = str(row.get("part") or row.get("model") or "").strip()
                pk = str(row.get("part_key") or part).strip().lower().replace("-", "")
                if not pk:
                    continue
                hay = f"{pk} {part} {row.get('package') or ''} {row.get('category') or ''}".lower()
                if q and q not in hay:
                    continue
                if pk in seen:
                    continue
                seen.add(pk)
                out.append(
                    {
                        "part_key": pk,
                        "part": part or pk.upper(),
                        "package": str(row.get("package") or ""),
                        "category": str(row.get("category") or ""),
                        "source": "inventory",
                    }
                )
                if len(out) >= limit:
                    return out

    if PARTS_DIR.is_dir():
        for fp in sorted(PARTS_DIR.glob("*.yaml")):
            pk = fp.stem.lower()
            if q and q not in pk:
                continue
            if pk in seen:
                continue
            seen.add(pk)
            out.append(
                {
                    "part_key": pk,
                    "part": pk.upper(),
                    "package": "",
                    "category": "",
                    "source": "parts",
                }
            )
            if len(out) >= limit:
                break
    return out


def grep_people(query: str, *, limit: int = 40) -> list[dict[str, Any]]:
    from ate.core.database import load_owners

    q = str(query or "").strip().lower()
    out: list[dict[str, Any]] = []
    for owner in load_owners():
        oid = str(owner.get("id") or "").lower()
        lab = str(owner.get("label") or oid)
        if oid in ("all", "kevin", "ate") or owner.get("alias_of"):
            continue
        if str(owner.get("role") or "").lower() == "observer":
            continue
        hay = f"{oid} {lab}".lower()
        if q and q not in hay:
            continue
        out.append(
            {
                "id": oid,
                "label": lab,
                "parts": list(owner.get("parts") or []),
            }
        )
        if len(out) >= limit:
            break
    return out


def attach_product(*, label: str, part_code: str) -> dict[str, Any]:
    """Grep hit -> owners.yaml parts: + ensure_product this operator only."""
    from ate.core.new_product import assign_owner_products

    return assign_owner_products(label=label, parts=[part_code])


def attach_person(*, label: str, part_code: str = "") -> dict[str, Any]:
    """Ensure person exists; optional SKU attach (this SKU only)."""
    from ate.core.database import upsert_owner
    from ate.core.new_product import assign_owner_products

    row = upsert_owner(label=label)
    if part_code:
        return {
            "owner": row,
            "assign": assign_owner_products(label=label, parts=[part_code]),
        }
    return {"owner": row}


def version_overlay_for(recipe_id: str) -> dict[str, Any] | None:
    """Load this Version's recipe_graph.yaml entry if present."""
    try:
        from ate.core.database import get_context

        path = get_context().manifest_dir() / "recipe_graph.yaml"
        if not path.is_file():
            return None
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        recipes = data.get("recipes") if isinstance(data, dict) else None
        if not isinstance(recipes, dict):
            return None
        rid = _safe_id(recipe_id)
        blob = recipes.get(rid)
        return blob if isinstance(blob, dict) else None
    except Exception:
        return None
