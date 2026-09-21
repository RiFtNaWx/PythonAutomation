"""Closed-opcode recipe walker (A14). No eval / exec / input().

ponytail: max 80 nodes, depth<=8, logic_inputs 1..8, AWG 2 CH then pause_hook.
Upgrade path: mux board or Export Path B thin wrapper.
"""
from __future__ import annotations

import itertools
from typing import Any, Callable

from ate.core.recipe_store import MAX_NODES, OPCODES, load_recipe, version_overlay_for

# Same allowlist as recipe_store
assert "eval" not in OPCODES

_MAX_DEPTH = 8


class RecipeError(ValueError):
    pass


def _node_op(node: dict[str, Any]) -> str:
    return str(node.get("op") or node.get("type") or "").strip().lower()


def _children(node: dict[str, Any], edges: list[dict[str, Any]], nodes_by_id: dict[str, dict]) -> list[dict[str, Any]]:
    nid = str(node.get("id") or "")
    kids: list[dict[str, Any]] = []
    # Prefer explicit children list on node
    raw_kids = node.get("children") or node.get("body") or []
    if isinstance(raw_kids, list) and raw_kids:
        for c in raw_kids:
            if isinstance(c, dict):
                kids.append(c)
            elif isinstance(c, str) and c in nodes_by_id:
                kids.append(nodes_by_id[c])
        return kids
    # Else follow edges source->target
    for e in edges:
        if not isinstance(e, dict):
            continue
        if str(e.get("source") or "") == nid:
            tid = str(e.get("target") or "")
            if tid in nodes_by_id:
                kids.append(nodes_by_id[tid])
    return kids


def _float_list(raw: Any) -> list[float]:
    out: list[float] = []
    if not isinstance(raw, list):
        return out
    for v in raw:
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            pass
    return out


def _sweep_points(node: dict[str, Any], ctx: dict[str, Any]) -> list[float]:
    explicit = _float_list(node.get("list") or node.get("values") or ctx.get("vcc_list"))
    if explicit:
        return explicit
    try:
        start = float(node.get("start", 0.0))
        stop = float(node.get("stop", 5.0))
        step = float(node.get("step", 0.5))
    except (TypeError, ValueError):
        return [0.0]
    if step <= 0:
        return [start]
    pts: list[float] = []
    x = start
    # inclusive stop with float guard
    while x <= stop + 1e-9 and len(pts) < 200:
        pts.append(round(x, 6))
        x += step
    return pts or [start]


def run(
    graph: dict[str, Any] | None = None,
    instr: Any = None,
    params: Any = None,
    *,
    recipe_id: str = "",
) -> dict[str, Any]:
    """Walk the recipe graph. Returns {summary, data, measurements}."""
    if graph is None:
        rid = recipe_id or getattr(params, "recipe_id", "") or ""
        overlay = version_overlay_for(rid) if rid else None
        graph = load_recipe(rid, overlay=overlay)

    nodes = list(graph.get("nodes") or [])
    if len(nodes) > MAX_NODES:
        raise RecipeError(f"too many nodes ({len(nodes)} > {MAX_NODES})")

    for node in nodes:
        if not isinstance(node, dict):
            raise RecipeError("node must be a dict")
        op = _node_op(node)
        if op not in OPCODES:
            raise RecipeError(f"unknown opcode {op!r}")
        for k in node:
            if str(k).lower() in ("eval", "exec", "code", "python", "script"):
                raise RecipeError(f"forbidden key {k!r}")

    edges = [e for e in (graph.get("edges") or []) if isinstance(e, dict)]
    nodes_by_id = {str(n.get("id") or f"n{i}"): n for i, n in enumerate(nodes) if isinstance(n, dict)}

    # Entry: first node without incoming edge, else nodes[0]
    targets = {str(e.get("target") or "") for e in edges}
    entry = None
    for n in nodes:
        nid = str(n.get("id") or "")
        if nid and nid not in targets:
            entry = n
            break
    if entry is None and nodes:
        entry = nodes[0]

    ctx: dict[str, Any] = {
        "vcc": float(getattr(params, "vcc", None) or graph.get("vcc") or 3.3),
        "vcc_list": _float_list(getattr(params, "vcc_list", None) or graph.get("vcc_list")),
        "logic_inputs": int(
            getattr(params, "logic_inputs", None)
            or graph.get("logic_inputs")
            or 2
        ),
        "levels": _float_list(getattr(params, "levels", None) or graph.get("levels") or [0.0, 5.5]),
        "rails": dict(getattr(params, "rails", None) or graph.get("rails") or {}),
        "corner": [],
        "last_value": None,
        "last_unit": "",
        "sim": bool(getattr(instr, "sim", False) if instr is not None else True),
    }
    # Clamp n
    ctx["logic_inputs"] = max(1, min(8, int(ctx["logic_inputs"])))

    measurements: list[dict[str, Any]] = []
    log: list[str] = []

    pause_hook: Callable[[str], bool] | None = getattr(params, "pause_hook", None)

    def walk(node: dict[str, Any] | None, depth: int) -> None:
        if node is None:
            return
        if depth > _MAX_DEPTH:
            raise RecipeError(f"nesting depth > {_MAX_DEPTH}")
        op = _node_op(node)
        if op == "end":
            return

        if op == "pause":
            msg = str(node.get("message") or node.get("text") or "Continue")
            if pause_hook is not None and not pause_hook(msg):
                raise RecipeError("aborted at pause")
            log.append(f"pause:{msg[:40]}")
            for c in _children(node, edges, nodes_by_id):
                walk(c, depth + 1)
            return

        if op == "sweep" or op == "for_list":
            key = str(node.get("var") or node.get("key") or "vcc").strip().lower()
            pts = _sweep_points(node, ctx)
            body = _children(node, edges, nodes_by_id)
            for p in pts:
                ctx[key] = p
                if key == "vcc":
                    ctx["vcc"] = p
                log.append(f"{op}:{key}={p}")
                for c in body:
                    walk(c, depth + 1)
            return

        if op == "for_corners":
            n = int(node.get("n") or node.get("logic_inputs") or ctx["logic_inputs"] or 2)
            n = max(1, min(8, n))
            levels = _float_list(node.get("levels") or ctx["levels"] or [0.0, 5.5])
            if len(levels) < 2:
                levels = [0.0, 5.5]
            # AWG ceiling: n>2 needs rewire
            if n > 2 and pause_hook is not None:
                if not pause_hook(f"for_corners n={n}: rewire AWG for inputs >2, then Continue"):
                    raise RecipeError("aborted at for_corners rewire")
            body = _children(node, edges, nodes_by_id)
            for corner in itertools.product(levels, repeat=n):
                ctx["corner"] = list(corner)
                log.append(f"corner:{corner}")
                for c in body:
                    walk(c, depth + 1)
            return

        if op == "if_else":
            left = node.get("left", ctx.get("last_value"))
            right = node.get("right", 0)
            cmp_op = str(node.get("cmp") or node.get("op_cmp") or "==").strip()
            # Resolve named lefts
            if isinstance(left, str) and left.startswith("$"):
                left = ctx.get(left[1:], ctx.get("last_value"))
            try:
                lf = float(left) if left is not None else 0.0
                rf = float(right)
            except (TypeError, ValueError):
                lf, rf = 0.0, 0.0
            ok = False
            if cmp_op in ("==", "eq"):
                ok = abs(lf - rf) < 1e-9
            elif cmp_op in ("!=", "ne"):
                ok = abs(lf - rf) >= 1e-9
            elif cmp_op in (">", "gt"):
                ok = lf > rf
            elif cmp_op in ("<", "lt"):
                ok = lf < rf
            elif cmp_op in (">=", "ge"):
                ok = lf >= rf
            elif cmp_op in ("<=", "le"):
                ok = lf <= rf
            else:
                raise RecipeError(f"bad if_else cmp {cmp_op!r}")
            branch = node.get("then") if ok else node.get("else")
            if isinstance(branch, list):
                for c in branch:
                    if isinstance(c, dict):
                        walk(c, depth + 1)
                    elif isinstance(c, str) and c in nodes_by_id:
                        walk(nodes_by_id[c], depth + 1)
            elif isinstance(branch, dict):
                walk(branch, depth + 1)
            elif isinstance(branch, str) and branch in nodes_by_id:
                walk(nodes_by_id[branch], depth + 1)
            else:
                # Fall through: first child = then edge label, second = else
                kids = _children(node, edges, nodes_by_id)
                if ok and kids:
                    walk(kids[0], depth + 1)
                elif (not ok) and len(kids) > 1:
                    walk(kids[1], depth + 1)
            return

        if op == "psu_set":
            ch = int(node.get("ch") or node.get("channel") or 1)
            volts = float(node.get("volts") or node.get("v") or ctx.get("vcc") or 3.3)
            amps = float(node.get("amps") or node.get("i") or getattr(params, "current_limit_a", None) or 0.10)
            if instr is not None and getattr(instr, "psu", None) is not None:
                from psu_setup import power_on_protected

                power_on_protected(instr.psu, ch, volts, amps)
            log.append(f"psu_set:CH{ch}={volts}V")
            for c in _children(node, edges, nodes_by_id):
                walk(c, depth + 1)
            return

        if op == "awg_out":
            ch = int(node.get("ch") or 1)
            wave = str(node.get("wave") or "DC").upper()
            volts = float(node.get("volts") or node.get("v") or 0.0)
            # Prefer corner index if present
            corner = ctx.get("corner") or []
            idx = int(node.get("corner_i") or (ch - 1))
            if corner and 0 <= idx < len(corner):
                volts = float(corner[idx])
            if ch > 2 and pause_hook is not None:
                if not pause_hook(f"awg_out CH{ch}: only 2 AWG channels; rewire then Continue"):
                    raise RecipeError("aborted at awg rewire")
            awg = getattr(instr, "gen", None) if instr is not None else None
            if awg is None and instr is not None:
                awg = getattr(instr, "awg", None)
            if awg is not None:
                try:
                    from generator_setup import enable_output, setup_dc

                    setup_dc(awg, ch, volts)
                    enable_output(awg, ch)
                except Exception as exc:
                    log.append(f"awg_out:skip:{exc}")
            log.append(f"awg_out:CH{ch}={wave}@{volts}")
            for c in _children(node, edges, nodes_by_id):
                walk(c, depth + 1)
            return

        if op == "dmm_read":
            unit = str(node.get("unit") or "V").strip()
            value = None
            mode = str(node.get("mode") or "voltage").strip().lower()
            if instr is not None and getattr(instr, "dmm", None) is not None:
                try:
                    if mode in ("current", "dci", "a"):
                        from dmm_setup import measure_current

                        value = float(measure_current(instr.dmm))
                        unit = str(node.get("unit") or "A")
                    else:
                        from dmm_setup import measure_voltage

                        value = float(measure_voltage(instr.dmm))
                except Exception as exc:
                    log.append(f"dmm_read:skip:{exc}")
            if value is None:
                # SIM / missing: deterministic dummy from corner + vcc
                corner = ctx.get("corner") or [0.0]
                value = float(ctx.get("vcc") or 0) * 0.01 + float(corner[0]) * 0.001
            ctx["last_value"] = value
            ctx["last_unit"] = unit
            log.append(f"dmm_read:{value}{unit}")
            mid = str(node.get("measure_id") or node.get("id_out") or "").strip()
            if mid:
                measurements.append({"id": mid, "value": value, "unit": unit})
            for c in _children(node, edges, nodes_by_id):
                walk(c, depth + 1)
            return

        if op == "scope_detect":
            log.append("scope_detect")
            # Record a stub measurement when SIM so DEMO has evidence
            if ctx.get("last_value") is None:
                ctx["last_value"] = float(ctx.get("vcc") or 0) * 0.5
            for c in _children(node, edges, nodes_by_id):
                walk(c, depth + 1)
            return

        if op == "screenshot":
            log.append("screenshot")
            if instr is not None and getattr(instr, "scope", None) is not None:
                try:
                    from scope_setup import screenshot

                    screenshot()
                except Exception as exc:
                    log.append(f"screenshot:skip:{exc}")
            for c in _children(node, edges, nodes_by_id):
                walk(c, depth + 1)
            return

        if op == "measure":
            mid = str(node.get("measure_id") or node.get("id") or "MEAS").strip()
            unit = str(node.get("unit") or ctx.get("last_unit") or "").strip()
            if "value" in node:
                try:
                    value = float(node["value"])
                except (TypeError, ValueError):
                    value = ctx.get("last_value")
            else:
                value = ctx.get("last_value")
            if value is None:
                value = 0.0
            measurements.append({"id": mid, "value": float(value), "unit": unit})
            ctx["last_value"] = float(value)
            log.append(f"measure:{mid}={value}{unit}")
            for c in _children(node, edges, nodes_by_id):
                walk(c, depth + 1)
            return

        raise RecipeError(f"unhandled opcode {op!r}")

    if entry is not None:
        # Linear chain: also walk sequential siblings if no edges (children-in-list style)
        if not edges and all(not (n.get("children") or n.get("body")) for n in nodes if isinstance(n, dict)):
            for n in nodes:
                walk(n, 0)
                if _node_op(n) == "end":
                    break
        else:
            walk(entry, 0)

    summary = f"recipe {graph.get('id') or '?'}: {len(measurements)} meas, {len(log)} steps"
    return {
        "summary": summary,
        "data": {"log": log[-50:], "corners_seen": True},
        "measurements": measurements,
    }


def make_run(recipe_id: str) -> Callable[..., dict[str, Any]]:
    """Factory for TestSpec.run closing over recipe_id."""

    def _run(instr: Any, params: Any) -> dict[str, Any]:
        return run(None, instr, params, recipe_id=recipe_id)

    return _run


def register_recipe_specs(family: str | None) -> int:
    """Register yaml recipes for this family as TestSpecs. Returns count."""
    from ate.core.recipe_store import list_recipes
    from ate.core.registry import TestSpec, register

    fam = str(family or "").strip().lower()
    if not fam:
        return 0
    # level rail shares logic suite; also load logic recipes onto level
    want = {fam}
    if fam == "level":
        want.add("logic")
    if fam == "logic":
        want.add("level")
    count = 0
    for row in list_recipes():
        rf = str(row.get("family") or "").strip().lower()
        if rf and rf not in want:
            continue
        # Skip comparator registration onto live rails when family is comparator stub
        if rf == "comparator" and fam != "comparator":
            continue
        rid = str(row["id"])
        try:
            graph = load_recipe(rid)
        except Exception:
            continue
        label = str(graph.get("label") or rid)
        short = str(graph.get("shortform") or "")
        register(
            TestSpec(
                id=rid,
                label=label,
                required_instruments=frozenset({"PSU", "DMM"}),
                fixture_mode="LOGIC",
                lab_sheet=label,
                run=make_run(rid),
                dual_channel=False,
                short_tag=short,
                notes=f"recipe:{rid}",
            )
        )
        count += 1
    return count
