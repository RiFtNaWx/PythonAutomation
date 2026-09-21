"""Fail-closed A14 recipe checks.

Run: python -m ate.core.check_recipe
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "ate" / "ui" / "web"
CANVAS_DIST = WEB / "canvas"


def main() -> int:
    errors: list[str] = []

    # Dist must exist for zip users (no npm)
    if not (CANVAS_DIST / "recipe-canvas.js").is_file():
        errors.append("ate/ui/web/canvas/recipe-canvas.js missing (commit Vite dist)")

    from ate.core.recipe_store import (
        OPCODES,
        list_recipes,
        load_recipe,
        preview_corners,
        validate_graph,
    )
    from ate.core.recipe_walk import RecipeError, run as recipe_run

    if "eval" in OPCODES or "exec" in OPCODES:
        errors.append("OPCODES must not include eval/exec")

    # Unknown opcode refused
    bad = {"id": "bad", "nodes": [{"id": "x", "op": "eval", "code": "1"}]}
    verr = validate_graph(bad)
    if not any("unknown" in e or "eval" in e for e in verr):
        errors.append(f"validate_graph must refuse eval, got {verr}")

    # 2^n corners
    prev = preview_corners(logic_inputs=2, levels=[0.0, 5.5])
    if prev.get("count") != 4:
        errors.append(f"preview_corners n=2 must be 4, got {prev.get('count')}")
    prev3 = preview_corners(logic_inputs=3, levels=[0.0, 1.0])
    if prev3.get("count") != 8:
        errors.append(f"preview_corners n=3 must be 8, got {prev3.get('count')}")

    # demo_corners walks
    rows = list_recipes(family="logic")
    ids = {r["id"] for r in rows}
    if "demo_corners" not in ids:
        errors.append("demo_corners recipe missing from list_recipes")
    else:
        graph = load_recipe("demo_corners")
        try:
            out = recipe_run(graph, None, None)
        except RecipeError as exc:
            errors.append(f"demo_corners walk failed: {exc}")
            out = {}
        meas = out.get("measurements") or []
        # 2 VCC x 4 corners = 8
        if len(meas) != 8:
            errors.append(f"demo_corners must yield 8 measurements, got {len(meas)}")
        if not all(m.get("id") == "CORNER_V" for m in meas):
            errors.append("demo_corners measurements must use CORNER_V id")

    # Walker refuses unknown at run time
    try:
        recipe_run({"id": "x", "nodes": [{"id": "a", "op": "not_an_op"}]}, None, None)
        errors.append("walker must raise on unknown opcode")
    except RecipeError:
        pass
    except Exception as exc:
        errors.append(f"walker unknown opcode wrong exc: {exc}")

    class _GenOnly:
        psu = None
        dmm = None
        scope = None
        gen = object()
        awg = None  # session stores AWG as .gen

    awg_graph = {
        "id": "awg_gen",
        "nodes": [
            {"id": "a", "op": "awg_out", "ch": 1, "volts": 0.0},
            {"id": "e", "op": "end"},
        ],
        "edges": [{"source": "a", "target": "e"}],
    }
    try:
        recipe_run(awg_graph, _GenOnly(), None)
    except Exception as exc:
        errors.append(f"awg_out must use instr.gen: {exc}")

    src = (REPO / "ate" / "core" / "recipe_walk.py").read_text(encoding="utf-8")
    if 'getattr(instr, "gen"' not in src:
        errors.append("recipe_walk awg_out must read instr.gen (session AWG handle)")

    # Register into logic family
    from ate.core.registry import clear, get, load_family

    clear()
    load_family("logic")
    if get("demo_corners") is None:
        errors.append("load_family(logic) must register demo_corners recipe TestSpec")

    # UI contract bits for Recipe tab
    index = WEB / "index.html"
    if index.is_file():
        html = index.read_text(encoding="utf-8")
        if 'data-page="recipe"' not in html:
            errors.append("Recipe tab data-page=recipe missing")
        if 'id="page-recipe"' not in html:
            errors.append("#page-recipe missing")
        if 'id="recipe-root"' not in html:
            errors.append("#recipe-root missing")
        if "canvas/recipe-canvas.js" not in html:
            errors.append("index.html must load canvas/recipe-canvas.js")
    else:
        errors.append("index.html missing")

    if errors:
        print("FAIL check_recipe:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("PASS check_recipe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
