"""Self-check for F23 / A16 detect-wrap-copy.

Run: python -m ate.core.check_test_detect
"""
from __future__ import annotations

import sys
from pathlib import Path

from ate.core import test_detect as td
from ate.core.paths import REPO_ROOT

FIXTURE_DIR = Path(__file__).resolve().parent / "_check_data"
FIXTURE_PY = FIXTURE_DIR / "detect_probe_source.py"


def _write_fixture() -> Path:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    FIXTURE_PY.write_text(
        '''\
"""Fixture for check_test_detect — not a live family module."""

def test_parameter():
    """Config helper: must not appear as a wrap row."""
    return [{"test_name": "dummy", "parameters": ["X"]}]


def test_detect_probe(instr, logger=None):
    """Clean golden: has instr, no stdin prompts."""
    psu = instr.psu
    return {"ok": True, "psu": bool(psu)}


def test_input_threshold(psu, dmm, logger=None, vcc_list=None):
    """Clean See Lin / Lim style: bare handles, not instr."""
    return {"VIH": 1.0, "psu": bool(psu), "dmm": bool(dmm)}


def _prompt(msg):
    return input(msg)


def test_ioz(instr, logger=None):
    """Dirty via helper: must be blocked even without a direct input() call."""
    _prompt("wire Y")
    return {}


def test_cpd(instr, logger=None):
    """Dirty golden: must be blocked."""
    input("Testing...")
    return {}
''',
        encoding="utf-8",
    )
    return FIXTURE_PY


def check_test_detect() -> list[str]:
    errors: list[str] = []
    import os
    import tempfile

    tmp_map = Path(tempfile.mkdtemp(prefix="ate_snip_")) / "snippet_map.yaml"
    os.environ["ATE_SNIPPET_MAP"] = str(tmp_map)
    fixture = _write_fixture()

    # Missing golden roots must not crash
    try:
        roots = td.load_golden_roots()
        listed = td.list_detected_tests(family="logic")
    except Exception as exc:
        errors.append(f"list_detected_tests crashed: {exc}")
        return errors
    if not tmp_map.is_file():
        errors.append("list_detected_tests must write snippet_map.yaml")
    if not listed.get("located"):
        errors.append("list_detected_tests must return located registered snippets")

    # Direct file scan
    rows = td.scan_file(fixture, registered=set())
    by_id = {r["id"]: r for r in rows}
    if "parameter" in by_id:
        errors.append("test_parameter config helper must not be listed")
    if "detect_probe" not in by_id:
        errors.append("expected detect_probe in scan_file results")
    else:
        if by_id["detect_probe"].get("blocked"):
            errors.append(
                f"detect_probe should be clean, got blocked_reason="
                f"{by_id['detect_probe'].get('blocked_reason')!r}"
            )
    if "input_threshold" not in by_id:
        errors.append("expected input_threshold (psu/dmm, unmatched) in scan_file")
    else:
        if by_id["input_threshold"].get("blocked"):
            errors.append(
                f"input_threshold(psu, dmm) must be wrap-ready, got "
                f"{by_id['input_threshold'].get('blocked_reason')!r}"
            )
    aliased = td.scan_file(fixture, registered={"input_thresholds"})
    if any(r.get("id") == "input_threshold" for r in aliased):
        errors.append("input_threshold must match registered input_thresholds")
    if "ioz" not in by_id:
        errors.append("expected ioz (dirty via _prompt) in scan_file results")
    else:
        if not by_id["ioz"].get("blocked"):
            errors.append("ioz that calls _prompt/input() must be blocked")
        if "input" not in str(by_id["ioz"].get("blocked_reason") or "").lower():
            errors.append(f"ioz blocked_reason should mention input(): {by_id['ioz']}")

    see_icc = REPO_ROOT / "goldens" / "see_lin" / "RS1G97" / "current_tests.py"
    if see_icc.is_file():
        see_rows = td.scan_file(
            see_icc,
            registered={"supply_current", "delta_supply_current", "input_leakage_sweep"},
        )
        see_ids = {r.get("id") for r in see_rows}
        if "icc" not in see_ids:
            errors.append("SeeLim test_icc must not alias onto supply_current")
        if "delta_icc" not in see_ids:
            errors.append("SeeLim test_delta_icc must not alias onto delta_supply_current")
        if "ii" not in see_ids:
            errors.append("SeeLim test_ii must not alias onto input_leakage_sweep")
        own = td.scan_file(see_icc, registered={"icc", "delta_icc", "ii"})
        own_icc = next((r for r in own if r.get("id") == "icc"), None)
        if own_icc is None:
            errors.append("SeeLim test_icc must stay visible when icc is already registered")
        elif not own_icc.get("matched"):
            errors.append("SeeLim test_icc should mark matched on the original file")
        elif "current_tests.py" not in str(own_icc.get("file") or ""):
            errors.append("SeeLim located icc must point at current_tests.py")
    if "cpd" not in by_id:
        errors.append("expected cpd (dirty) in scan_file results")
    else:
        if not by_id["cpd"].get("blocked"):
            errors.append("cpd with input() must be blocked")
        if "input" not in str(by_id["cpd"].get("blocked_reason") or "").lower():
            errors.append(f"cpd blocked_reason should mention input(): {by_id['cpd']}")

    vendor_py = FIXTURE_DIR / "detect_vendor_source.py"
    vendor_py.write_text(
        "from Lim.foo import bar\n\ndef test_vendor_probe(instr):\n    return {}\n",
        encoding="utf-8",
    )
    vrows = td.scan_file(vendor_py, registered=set())
    vp = next((r for r in vrows if r.get("id") == "vendor_probe"), None)
    if vp is None:
        errors.append("expected vendor_probe in vendor fixture scan")
    elif not vp.get("blocked") or "lim" not in str(vp.get("blocked_reason") or "").lower():
        errors.append(f"vendor import Lim must block wrap: {vp}")

    extra_src = fixture.read_text(encoding="utf-8")
    if "test_detect_extra" not in extra_src:
        fixture.write_text(
            extra_src + "\n\ndef test_detect_extra(instr, logger=None):\n    return {\"extra\": 1}\n",
            encoding="utf-8",
        )
    extra_rows = td.scan_file(fixture, registered=set())
    if "detect_extra" not in {r.get("id") for r in extra_rows}:
        errors.append("new def test_* must appear on rescan")

    # Refuse dirty wrap
    try:
        td.wrap_detected_test(
            file=str(fixture),
            fn="test_cpd",
            family="demo_ingest",
        )
        errors.append("wrap of dirty test_cpd must raise")
    except ValueError as exc:
        if "input" not in str(exc).lower():
            errors.append(f"dirty wrap error should mention input(): {exc}")
    except Exception as exc:
        errors.append(f"dirty wrap unexpected: {exc}")

    try:
        td.wrap_detected_test(
            file=str(fixture),
            fn="test_ioz",
            family="demo_ingest",
        )
        errors.append("wrap of dirty test_ioz via _prompt must raise")
    except ValueError as exc:
        if "input" not in str(exc).lower():
            errors.append(f"dirty helper wrap error should mention input(): {exc}")
    except Exception as exc:
        errors.append(f"dirty helper wrap unexpected: {exc}")

    # Clean wrap into demo_ingest -- pointer trigger, no imported_*.py
    pkg = REPO_ROOT / "ate" / "tests" / "demo_ingest"
    mod = pkg / "imported_detect_probe.py"
    init = pkg / "__init__.py"
    init_bak = init.read_text(encoding="utf-8") if init.is_file() else ""
    try:
        try:
            td.wrap_detected_test(
                file=str(vendor_py),
                fn="test_vendor_probe",
                family="demo_ingest",
            )
            errors.append("wrap of vendor Lim import must raise")
        except ValueError as exc:
            if "lim" not in str(exc).lower() and "vendor" not in str(exc).lower():
                errors.append(f"vendor wrap error should name Lim: {exc}")
        except Exception as exc:
            errors.append(f"vendor wrap unexpected: {exc}")

        out = td.wrap_detected_test(
            file=str(fixture),
            fn="test_detect_probe",
            family="demo_ingest",
        )
        if not out.get("ok") or out.get("id") != "detect_probe":
            errors.append(f"clean wrap failed: {out}")
        if out.get("mode") not in ("trigger", "enable"):
            errors.append(f"clean wrap must return mode trigger/enable, got {out.get('mode')}")
        if not (out.get("snippet") or {}).get("file"):
            errors.append(f"clean wrap must return snippet file:line: {out}")
        if mod.is_file():
            errors.append("wrap must not write imported_detect_probe.py")
        from ate.core.registry import all_tests, load_family
        from types import SimpleNamespace

        load_family("demo_ingest")
        ids = {t.id for t in all_tests()}
        if "detect_probe" not in ids:
            errors.append("detect_probe missing from demo_ingest registry after wrap")
        spec = next((t for t in all_tests() if t.id == "detect_probe"), None)
        if spec is not None:
            triggered = spec.run(SimpleNamespace(psu=object(), dmm=None), None)
            if "imported scaffold" in str(triggered.get("summary") or "").lower():
                errors.append("trigger must not return imported scaffold")
            if (triggered.get("data") or {}).get("ok") is not True:
                errors.append(f"trigger must return original fixture result, got {triggered}")
    except Exception as exc:
        errors.append(f"clean wrap failed: {exc}")
    finally:
        if mod.is_file():
            errors.append("wrap left imported_detect_probe.py on disk")
            mod.unlink()
        if init_bak:
            init.write_text(init_bak, encoding="utf-8")
        else:
            if init.is_file():
                lines = [
                    ln
                    for ln in init.read_text(encoding="utf-8").splitlines()
                    if "imported_detect_probe" not in ln
                ]
                init.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        try:
            from ate.core.registry import load_family

            load_family("demo_ingest")
        except Exception:
            pass

    # Cross-family copy refused
    try:
        td.enable_tests_on_part(
            dest_part="rs1g07",
            test_ids=["slew"],
            source_part="rs622",
        )
        errors.append("cross-family enable must refuse")
    except ValueError as exc:
        if "cross-family" not in str(exc).lower() and "family" not in str(exc).lower():
            errors.append(f"cross-family error unclear: {exc}")
    except Exception as exc:
        errors.append(f"cross-family unexpected: {exc}")

    # Missing root skip: temp non-existent path in config is fine via load_golden_roots
    missing = [r for r in roots if not r.get("exists")]
    _ = missing  # expected; not an error

    # Operator isolation: this person only; never merge Ariff
    import shutil
    import tempfile

    from ate.core import database as dbmod
    from ate.core import paths as pathmod
    from ate.core.database import set_context
    from ate.core.paths import PARTS_DIR

    part_yaml = PARTS_DIR / "rs1g07.yaml"
    yaml_before = part_yaml.read_text(encoding="utf-8") if part_yaml.is_file() else ""
    tmp = Path(tempfile.mkdtemp(prefix="ate_campaign_tests_"))
    old_root = pathmod.TEST_DB_ROOT
    old_db_root = dbmod.TEST_DB_ROOT
    old_active = dbmod._active
    try:
        pathmod.TEST_DB_ROOT = tmp / "#Test_Database"
        dbmod.TEST_DB_ROOT = pathmod.TEST_DB_ROOT
        pathmod.TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
        set_context(
            component="Logic",
            part="RS1G07",
            package="SOT23",
            operator="Eugene",
            version="Version_1",
            part_key="rs1g07",
        )
        from ate.core.database import get_context

        ctx = get_context()
        man = ctx.manifest_dir()
        man.mkdir(parents=True, exist_ok=True)
        (man / "test_catalog.yaml").write_text(
            "enabled_tests:\n  - supply_current\n",
            encoding="utf-8",
        )
        v2 = ctx.root().parent / "Version_2" / "_manifest"
        v2.mkdir(parents=True, exist_ok=True)
        (v2 / "test_catalog.yaml").write_text(
            "enabled_tests:\n  - supply_current\n  - output_voltage\n",
            encoding="utf-8",
        )
        ariff = ctx.root().parent.parent / "Ariff" / "Version_1" / "_manifest"
        ariff.mkdir(parents=True, exist_ok=True)
        (ariff / "test_catalog.yaml").write_text(
            "enabled_tests:\n  - ten\n",
            encoding="utf-8",
        )
        snap = td.list_campaign_tests()
        if not snap.get("ok"):
            errors.append(f"list_campaign_tests: {snap}")
        else:
            skipped = {s.get("operator") for s in (snap.get("skipped_operators") or [])}
            if "Ariff" not in skipped:
                errors.append(f"must skip Ariff, got {snap.get('skipped_operators')}")
            missing_ids = set(snap.get("missing") or [])
            current = set(snap.get("current") or [])
            if "ten" in missing_ids or "ten" in current:
                errors.append("must not merge Ariff ten into Eugene campaign")
            if "output_voltage" not in missing_ids:
                errors.append(
                    f"Eugene Version_2 output_voltage should be missing on V1, got {sorted(missing_ids)}"
                )
        try:
            td.set_campaign_enabled_tests(["supply_current"], family="opamp")
            errors.append("cross-category set_campaign_enabled_tests must refuse")
        except ValueError as exc:
            if "category" not in str(exc).lower() and "family" not in str(exc).lower():
                errors.append(f"same-category error unclear: {exc}")
        added = td.add_missing_campaign_tests()
        got = set(added.get("enabled_tests") or []) | set(added.get("added") or [])
        if "ten" in got:
            errors.append("add_missing must not take Ariff ten")
        if "output_voltage" not in set(added.get("added") or []) and "output_voltage" not in set(
            added.get("enabled_tests") or []
        ):
            errors.append("add_missing should add Eugene V2 output_voltage")
        ariff_txt = (ariff / "test_catalog.yaml").read_text(encoding="utf-8")
        if "output_voltage" in ariff_txt or "supply_current" in ariff_txt:
            errors.append("must not write Ariff catalog")
        if "ten" not in ariff_txt:
            errors.append("Ariff catalog must stay ten")
        if part_yaml.is_file() and part_yaml.read_text(encoding="utf-8") != yaml_before:
            errors.append("must not write shared parts/rs1g07.yaml")
        try:
            td.wrap_detected_test(
                file=str(fixture),
                fn="test_detect_probe",
                family="opamp",
            )
            errors.append("wrap opamp into logic campaign must refuse")
        except ValueError as exc:
            if "category" not in str(exc).lower() and "family" not in str(exc).lower():
                errors.append(f"wrap category error unclear: {exc}")
    except Exception as exc:
        errors.append(f"campaign isolation crashed: {exc}")
    finally:
        pathmod.TEST_DB_ROOT = old_root
        dbmod.TEST_DB_ROOT = old_db_root
        dbmod._active = old_active
        shutil.rmtree(tmp, ignore_errors=True)

    import tempfile as _tf

    prune_root = Path(_tf.mkdtemp(prefix="ate_scan_"))
    try:
        (prune_root / "keep.py").write_text(
            "def test_keep(instr):\n    return 1\n", encoding="utf-8"
        )
        venv_py = prune_root / "venv" / "Lib" / "site-packages" / "junk.py"
        venv_py.parent.mkdir(parents=True, exist_ok=True)
        venv_py.write_text("def test_pandas(instr):\n    return 1\n", encoding="utf-8")
        walked = td._iter_py_files(prune_root)
        if any("venv" in p.parts or "site-packages" in p.parts for p in walked):
            errors.append("_iter_py_files must prune venv/site-packages while walking")
        if not any(p.name == "keep.py" for p in walked):
            errors.append("_iter_py_files must still see files outside venv")
    finally:
        shutil.rmtree(prune_root, ignore_errors=True)

    if td.author_for_path("goldens/eugene/Soo/logic_tests.py") != "soo":
        errors.append("Soo files under eugene/Soo must author=soo")
    if td.author_for_path("goldens/see_lin/RS1G97/current_tests.py") != "seelim":
        errors.append("see_lin files must author=seelim")
    own = td.list_detected_tests(family="logic", operator="SeeLim", allow_others=False)
    if own.get("author") != "seelim":
        errors.append(f"SeeLim scan author must be seelim, got {own.get('author')}")
    foreign = [
        r for r in (own.get("detected") or []) + (own.get("located") or [])
        if str(r.get("author") or "") in ("ariff", "eugene", "soo")
    ]
    if foreign:
        errors.append(
            f"SeeLim scan must not list other authors until allow_others, got {foreign[:2]}"
        )
    ignored = td.list_detected_tests(
        family="logic", operator="SeeLim", author="ariff", allow_others=False
    )
    if ignored.get("author") != "seelim":
        errors.append("without allow_others, author=ariff must be ignored")
    mixed = td.list_detected_tests(
        family="logic", operator="SeeLim", author="ariff", allow_others=True
    )
    if mixed.get("author") != "ariff":
        errors.append(f"allow_others author=ariff must scan ariff, got {mixed.get('author')}")

    ariff_tmp = Path(tempfile.mkdtemp(prefix="ate_ariff_")) / "ariff" / "clean_tests.py"
    try:
        ariff_tmp.parent.mkdir(parents=True, exist_ok=True)
        ariff_tmp.write_text(
            "def test_foreign_probe(instr, logger=None):\n    return {\"ok\": True}\n",
            encoding="utf-8",
        )
        try:
            td.wrap_detected_test(
                file=str(ariff_tmp),
                fn="test_foreign_probe",
                family="demo_ingest",
                operator="SeeLim",
            )
            errors.append("wrap of Ariff golden as SeeLim must refuse without allow_others")
        except ValueError as exc:
            low = str(exc).lower()
            if "allow" not in low and "golden" not in low and "ariff" not in low:
                errors.append(f"foreign wrap error unclear: {exc}")
        allowed = td.wrap_detected_test(
            file=str(ariff_tmp),
            fn="test_foreign_probe",
            family="demo_ingest",
            operator="SeeLim",
            allow_others=True,
        )
        if not allowed.get("ok"):
            errors.append(f"allow_others wrap of Ariff golden must work, got {allowed}")
    except Exception as exc:
        errors.append(f"foreign wrap check crashed: {exc}")
    finally:
        shutil.rmtree(ariff_tmp.parent.parent, ignore_errors=True)

    return errors


def main() -> int:
    errs = check_test_detect()
    if errs:
        print("FAIL check_test_detect:")
        for e in errs:
            print(f"  - {e}")
        return 1
    print("OK check_test_detect: clean wrap / dirty block / missing root skip / cross-family refuse / operator isolation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
