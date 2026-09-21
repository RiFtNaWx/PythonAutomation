"""Datasheet min/typ/max for one part. Pass/fail lives here, not in each TestSpec.

Specs are ate/config/limits/<key>.yaml then part yaml `specs:`.
Never a RUN-IC catalog dump into #Test_Database.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Optional

import yaml

from ate.core.paths import CONFIG_DIR, PARTS_DIR

LIMITS_DIR = CONFIG_DIR / "limits"


def _num(raw: Any) -> Optional[float]:
    if raw is None or raw == "":
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def load_part_yaml(part_key: str = "") -> dict[str, Any]:
    pk = str(part_key or "").strip().lower()
    if not pk:
        return {}
    path = PARTS_DIR / f"{pk}.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def load_part_specs(part_key: str = "", overlay: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    pk = str(part_key or "").strip().lower()
    rows: list[Any] = []
    lim = LIMITS_DIR / f"{pk}.yaml"
    if lim.is_file():
        blob = yaml.safe_load(lim.read_text(encoding="utf-8")) or {}
        if isinstance(blob, dict) and isinstance(blob.get("specs"), list):
            rows.extend(blob["specs"])
    data = load_part_yaml(pk)
    if isinstance(data.get("specs"), list):
        rows.extend(data["specs"])
    stacked: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        item = dict(row)
        item["id"] = str(item["id"]).strip()
        item["min"] = _num(item.get("min"))
        item["max"] = _num(item.get("max"))
        item["typ"] = _num(item.get("typ"))
        if item.get("pass_mode"):
            item["pass_mode"] = str(item["pass_mode"]).strip().lower().replace("_", "-")
        stacked[item["id"]] = item
    if isinstance(overlay, dict):
        pm = overlay.get("pass_mode") if isinstance(overlay.get("pass_mode"), dict) else {}
        for sid, mode in pm.items():
            key = str(sid).strip()
            if key not in stacked:
                continue
            stacked[key]["pass_mode"] = str(mode).strip().lower().replace("_", "-")
    return list(stacked.values())


def infer_pass_mode(spec: Any = None, **_kwargs: Any) -> str:
    """min-only / max-only / range from spec id + min/max. No invented PASS."""
    row = spec if isinstance(spec, dict) else {}
    raw = str(row.get("pass_mode") or "").strip().lower().replace("_", "-")
    if raw in ("min-only", "max-only", "range", "fail-open", "unspec"):
        return raw
    sid = str(row.get("id") or "").upper().replace(" ", "")
    if sid.startswith("VIH") or sid.startswith("VOH") or sid.startswith("VTPLUS") or sid.startswith("VT+"):
        return "min-only"
    if (
        sid.startswith("VIL")
        or sid.startswith("VOL")
        or sid.startswith("ICC")
        or sid.startswith("II")
        or sid.startswith("IOZ")
        or sid.startswith("DELTA")
    ):
        return "max-only"
    if row.get("min") is not None and row.get("max") is None:
        return "min-only"
    if row.get("max") is not None and row.get("min") is None:
        return "max-only"
    if row.get("min") is not None and row.get("max") is not None:
        return "range"
    return "unspec"


def apply_version_spec_overlay(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge this Version `_manifest/test_params.yaml` specs onto limits yaml."""
    try:
        from ate.core.database import load_test_params

        blob = load_test_params()
    except Exception:
        return rows
    tests = blob.get("tests") if isinstance(blob, dict) else {}
    if not isinstance(tests, dict) or not tests:
        return rows
    stacked = {
        str(r.get("id")): dict(r)
        for r in rows
        if isinstance(r, dict) and r.get("id")
    }
    order = list(stacked.keys())
    for _tid, block in tests.items():
        if not isinstance(block, dict):
            continue
        for row in block.get("specs") or []:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            sid = str(row["id"]).strip()
            cur = dict(stacked.get(sid) or {"id": sid})
            for key in ("min", "max", "typ"):
                if row.get(key) in (None, ""):
                    continue
                n = _num(row.get(key))
                if n is not None:
                    cur[key] = n
            if row.get("unit"):
                cur["unit"] = str(row["unit"])
            if sid not in stacked:
                order.append(sid)
            stacked[sid] = cur
    return [stacked[sid] for sid in order if sid in stacked]


def test_info_map(part_key: str = "") -> dict[str, dict[str, Any]]:
    pk = str(part_key or "").strip().lower()
    out: dict[str, dict[str, Any]] = {}

    def _eat(block: Any) -> None:
        if not isinstance(block, dict):
            return
        for key, meta in block.items():
            if isinstance(meta, dict):
                out[str(key)] = dict(meta)
            elif isinstance(meta, str) and meta.strip():
                out[str(key)] = {"description": meta.strip()}

    lim = LIMITS_DIR / f"{pk}.yaml"
    if lim.is_file():
        blob = yaml.safe_load(lim.read_text(encoding="utf-8")) or {}
        if isinstance(blob, dict):
            _eat(blob.get("test_info"))
    _eat(load_part_yaml(pk).get("test_info"))
    return out


def load_part_datasheet(part_key: str = "") -> dict[str, Any]:
    pk = str(part_key or "").strip().lower()
    ds: dict[str, Any] = {}
    yml = load_part_yaml(pk).get("datasheet")
    if isinstance(yml, dict):
        ds.update(yml)
    lim = LIMITS_DIR / f"{pk}.yaml"
    if lim.is_file():
        blob = yaml.safe_load(lim.read_text(encoding="utf-8")) or {}
        if isinstance(blob, dict) and isinstance(blob.get("datasheet"), dict):
            ds.update(blob["datasheet"])
    return ds


PROBE_CH_LETTERS = "ABCDEFGH"  # DUT probe positions (CHA..), not PSU CH1.


def probe_channel_ids() -> list[str]:
    return [f"CH{letter}" for letter in PROBE_CH_LETTERS]


def _norm_probe_ch(token: Any) -> str:
    t = str(token or "").strip().upper().replace("CHANNEL", "").replace(" ", "")
    t = t.replace("_", "")
    if t.startswith("CH") and len(t) >= 3:
        rest = t[2:]
        if rest.isdigit():
            n = int(rest)
            if 1 <= n <= len(PROBE_CH_LETTERS):
                return f"CH{PROBE_CH_LETTERS[n - 1]}"
        if len(rest) == 1 and rest in PROBE_CH_LETTERS:
            return f"CH{rest}"
    if len(t) == 1 and t in PROBE_CH_LETTERS:
        return f"CH{t}"
    if t.isdigit():
        n = int(t)
        if 1 <= n <= len(PROBE_CH_LETTERS):
            return f"CH{PROBE_CH_LETTERS[n - 1]}"
    return ""


def channel_prompt_label(channel: str) -> str:
    ch = _norm_probe_ch(channel) or "CHA"
    return f"Channel {ch[-1]}"


def normalize_probe_channels(raw: Any) -> list[str]:
    parsed = set(_parse_probe_channels(raw))
    return [c for c in probe_channel_ids() if c in parsed]


def _parse_probe_channels(raw: Any) -> list[str]:
    if isinstance(raw, str):
        raw = [p for p in raw.replace(",", " ").split() if p]
    if not isinstance(raw, (list, tuple)):
        return []
    out: list[str] = []
    for item in raw:
        ch = _norm_probe_ch(item)
        if ch and ch not in out:
            out.append(ch)
    return out


def probe_channels_for_part(part_key: str = "", family: str = "") -> list[str]:
    """Probe CHA/CHB for this SKU. Not PSU CH1/CH2 and not VCCA/VCCB.

    Explicit part yaml `channels:` / `probe_channels:` or datasheet.channels wins.
    Else OpAmp is CHA+CHB; Logic / switch / level / power are CHA only.
    """
    data = load_part_yaml(part_key)
    raw = data.get("channels")
    if raw is None:
        raw = data.get("probe_channels")
    ds = load_part_datasheet(part_key)
    if raw is None:
        raw = ds.get("channels") if isinstance(ds, dict) else None
    if raw is None and isinstance(ds, dict):
        raw = ds.get("probe_channels")
    parsed = _parse_probe_channels(raw)
    if parsed:
        return parsed
    fam = str(family or data.get("component") or data.get("family") or "").strip().lower()
    fam = fam.replace(" ", "").replace("_", "")
    if fam in ("opamp", "opa", "buffer", "operationalamplifier", "lownoiseopamp"):
        return ["CHA", "CHB"]
    return ["CHA"]


def judge_value(value: Any, mn: Any, mx: Any, pass_mode: str | None = None) -> str:
    """pass / fail / unspec. typ is display-only."""
    mode = str(pass_mode or "").strip().lower().replace("_", "-")
    if mode == "unspec":
        return "unspec"
    if mode == "min-only":
        mx = None
    elif mode == "max-only":
        mn = None
    elif mode == "fail-open" and _num(mn) is None and _num(mx) is None:
        return "fail"
    v = _num(value)
    lo = _num(mn)
    hi = _num(mx)
    if v is not None and math.isnan(v):
        return "fail" if (lo is not None or hi is not None) else "unspec"
    if v is None or (lo is None and hi is None):
        return "unspec"
    if lo is not None and v < lo:
        return "fail"
    if hi is not None and v > hi:
        return "fail"
    return "pass"


def _test_aliases(tid: str) -> set[str]:
    t = str(tid or "").strip().lower()
    if not t:
        return set()
    if t in ("supply_current", "supply_current_sweep"):
        return {"supply_current", "supply_current_sweep"}
    if t in ("voh_load", "voh"):
        return {"voh_load", "voh"}
    if t in ("vol_load", "vol"):
        return {"vol_load", "vol"}
    if t in ("input_threshold", "input_thresholds", "vih_vil", "vth"):
        return {"input_threshold", "input_thresholds", "vih_vil", "vth"}
    return {t}


def _spec_for(specs: list[dict[str, Any]], meas_id: str, test_id: str = "") -> dict[str, Any] | None:
    want = str(meas_id or "").strip().lower()
    aliases = _test_aliases(test_id)
    for row in specs:
        rid = str(row.get("id") or "").strip().lower()
        if rid == want:
            return row
    if aliases:
        tid = str(test_id or "").strip().lower()
        if want in aliases or want == tid:
            for row in specs:
                if str(row.get("test") or "").strip().lower() in aliases:
                    return row
    return None


def enrich_measurement(
    raw: dict[str, Any],
    *,
    specs: list[dict[str, Any]] | None = None,
    test_id: str = "",
    part_key: str = "",
    **_kw: Any,
) -> dict[str, Any]:
    row = dict(raw)
    sid = str(row.get("id") or row.get("name") or test_id or "").strip()
    if sid:
        row["id"] = sid
    if specs is None and part_key:
        specs = load_part_specs(part_key)
    spec = _spec_for(specs or [], sid, test_id)
    if spec:
        if row.get("min") is None and spec.get("min") is not None:
            row["min"] = spec["min"]
        if row.get("max") is None and spec.get("max") is not None:
            row["max"] = spec["max"]
        if row.get("typ") is None and spec.get("typ") is not None:
            row["typ"] = spec["typ"]
        if not row.get("unit") and spec.get("unit"):
            row["unit"] = spec["unit"]
        if not row.get("source") and spec.get("source"):
            row["source"] = spec["source"]
        if not row.get("pass_mode") and spec.get("pass_mode"):
            row["pass_mode"] = spec["pass_mode"]
    row["result"] = judge_value(
        row.get("value"), row.get("min"), row.get("max"), pass_mode=row.get("pass_mode")
    )
    if row.get("greenable") is False and row.get("result") in ("pass", "fail"):
        row["result"] = "unspec"
    return row


def _flatten_numbers(blob: Any, prefix: str = "") -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(blob, dict):
        if "value" in blob and (blob.get("id") or blob.get("name") or prefix):
            item = dict(blob)
            item.setdefault("id", blob.get("id") or blob.get("name") or prefix)
            out.append(item)
            return out
        for key, val in blob.items():
            if key in ("screenshot", "screenshots", "artifacts", "summary", "message"):
                continue
            kid = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                out.append({"id": kid, "value": val})
            elif isinstance(val, (dict, list)):
                out.extend(_flatten_numbers(val, kid))
    elif isinstance(blob, list):
        for i, val in enumerate(blob):
            out.extend(_flatten_numbers(val, f"{prefix}[{i}]" if prefix else str(i)))
    return out


def _alias_legacy_ids(
    rows: list[dict[str, Any]], specs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Map Soo IDD_mA onto datasheet ICC_uA when that spec exists for the part."""
    have = {str(s.get("id") or "").strip() for s in specs}
    if "ICC_uA" not in have:
        return rows
    out: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        if str(row.get("id") or "") == "IDD_mA":
            row["id"] = "ICC_uA"
            if row.get("value") is not None:
                try:
                    row["value"] = float(row["value"]) * 1000.0
                except (TypeError, ValueError):
                    pass
            row["unit"] = "uA"
        out.append(row)
    return out


def _prefer_spec_ids(
    rows: list[dict[str, Any]], specs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    ids = {str(s.get("id") or "").strip().lower() for s in specs}
    if not ids:
        return rows
    return [r for r in rows if str(r.get("id") or "").strip().lower() in ids]


def measurements_from_result(
    data: Any,
    *,
    test_id: str = "",
    part_key: str = "",
) -> list[dict[str, Any]]:
    specs = apply_version_spec_overlay(load_part_specs(part_key))
    blob = data if isinstance(data, dict) else {}
    raw = blob.get("measurements")
    rows: list[dict[str, Any]]
    if isinstance(raw, list) and raw:
        rows = [x for x in raw if isinstance(x, dict)]
    else:
        inner = blob.get("data") if isinstance(blob.get("data"), dict) else blob
        rows = _flatten_numbers(inner)
        if not rows and specs:
            hit = _spec_for(specs, test_id, test_id)
            if hit:
                rows = [{"id": hit["id"]}]
    rows = _alias_legacy_ids(rows, specs)
    rows = _prefer_spec_ids(rows, specs)
    out = [enrich_measurement(r, specs=specs, test_id=test_id) for r in rows]
    return [m for m in out if m.get("id")]


def mock_demo_measurements(test_id: str, *, part_key: str = "") -> list[dict[str, Any]]:
    specs = apply_version_spec_overlay(load_part_specs(part_key))
    tid = str(test_id or "").strip().lower()
    aliases = _test_aliases(tid)
    picked = [
        s
        for s in specs
        if str(s.get("test") or "").strip().lower() in aliases
        or str(s.get("id") or "").strip().lower() == tid
    ]
    if not picked:
        return []
    out: list[dict[str, Any]] = []
    for spec in picked:
        val = spec.get("typ")
        if val is None and spec.get("min") is not None and spec.get("max") is not None:
            val = (float(spec["min"]) + float(spec["max"])) / 2.0
        elif val is None and spec.get("max") is not None:
            val = float(spec["max"])
        elif val is None and spec.get("min") is not None:
            val = float(spec["min"])
        out.append(
            enrich_measurement(
                {"id": spec["id"], "value": val, "unit": spec.get("unit") or ""},
                specs=specs,
                test_id=test_id,
            )
        )
    return out


def any_fail(measurements: list[dict[str, Any]] | None) -> bool:
    return any(str(m.get("result") or "") == "fail" for m in (measurements or []) if isinstance(m, dict))
