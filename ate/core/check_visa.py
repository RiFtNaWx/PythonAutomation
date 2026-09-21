"""Fail-closed: PyVISA backend, ASRL skip, one shared RM, SIM still skips USB.

Run: python -m ate.core.check_visa
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

from ate.core.paths import REPO_ROOT


def _sim_load_timing_and_control() -> list[str]:
    """SIM PyVISA stand-in: load INF, timeouts, PSU protect, loopback. No USB."""
    import time

    from ate.instruments.session import Instruments
    from ate.instruments.sim import loopback_check, reset_bus
    from dmm_setup import dmm_setup_current, dmm_setup_voltage
    from generator_setup import (
        is_banned_awg_scpi,
        query_frequency,
        set_frequency,
        set_output_load,
        setup_dc,
        setup_square,
        stop_output,
    )
    from psu_setup import power_off, power_on, power_on_protected, resolve_protect

    errors: list[str] = []
    t0 = time.perf_counter()
    sim = Instruments.simulated()
    load_s = time.perf_counter() - t0
    if load_s > 2.0:
        errors.append(f"SIM session load {load_s:.2f}s (must not hang like USB viOpen)")
    if getattr(sim.gen, "timeout", 0) != 3000:
        errors.append(f"SIM AWG default timeout want 3000 got {sim.gen.timeout}")
    sim.scope.timeout = 20000
    sim.psu.timeout = 12000
    sim.gen.timeout = 12000
    sim.dmm.timeout = 12000
    if sim.scope.timeout != 20000 or sim.dmm.timeout != 12000:
        errors.append("SIM timeout control failed (MSO 20s / DMM 12s)")

    reset_bus()
    awg = sim.gen
    set_output_load(awg, 1, "INF")
    set_output_load(awg, 2, "INF")
    setup_dc(awg, 1, 1.65)
    setup_square(awg, 2, 1000, 3.3, 1.65)
    joined = " ".join(str(w).upper() for w in awg.writes)
    if not any("LOAD INF" in str(w).upper() for w in awg.writes):
        errors.append("set_output_load must write :OUTPn:LOAD INF")
    if any(tok in joined for tok in (":OUTP3", ":OUTP4", "DCYC", ":SOUR1:FREQ")):
        errors.append(f"AWG SIM wrote banned -116 header: {awg.writes}")
    err = str(awg.query("SYST:ERR?")).strip()
    if not err.startswith("0"):
        errors.append(f"AWG SYST:ERR after LOAD/APPL want 0 got {err!r}")
    if not is_banned_awg_scpi(":SOUR1:FREQ 1000"):
        errors.append("is_banned_awg_scpi must flag :SOUR1:FREQ")
    if is_banned_awg_scpi(":SOUR1:APPL:SQU 1000,3.3,1.65,0"):
        errors.append("is_banned_awg_scpi must allow APPL:SQU")
    if not is_banned_awg_scpi(":OUTP3 OFF") or not is_banned_awg_scpi(
        ":SOUR1:FUNC:SQU:DCYC 50"
    ):
        errors.append("is_banned_awg_scpi must flag OUTP3 and DCYC")
    awg.write(":SOUR1:FREQ 1000")
    err_bad = str(awg.query("SYST:ERR?")).strip()
    if not err_bad.startswith("-116"):
        errors.append(f"SIM AWG FREQ must SYST:ERR -116 got {err_bad!r}")
    err_clr = str(awg.query("SYST:ERR?")).strip()
    if not err_clr.startswith("0"):
        errors.append("SYST:ERR must clear after read")
    n1 = len(awg.writes)
    set_frequency(awg, 2, 2000.0)
    new = awg.writes[n1:]
    if any(is_banned_awg_scpi(str(w)) for w in new):
        errors.append(f"set_frequency sent banned header {new}")
    if not any("APPL:" in str(w).upper() for w in new):
        errors.append("set_frequency must re-APPL (no standalone FREQ)")
    got_f = query_frequency(awg, 2)
    if abs(float(got_f) - 2000.0) > 1.0:
        errors.append(f"query_frequency after set want 2000 got {got_f}")
    err_set = str(awg.query("SYST:ERR?")).strip()
    if not err_set.startswith("0"):
        errors.append(f"set_frequency SYST:ERR want 0 got {err_set!r}")
    try:
        setup_square(awg, 3, 1000, 1.0, 0.0)
        errors.append("AWG CH3 must raise (OUTP3 is Error 116)")
    except ValueError:
        pass

    psu = sim.psu
    try:
        power_on(psu, 1, 3.3)
        errors.append("power_on must stay banned")
    except RuntimeError:
        pass
    try:
        resolve_protect(5.0, 0.1, ovp=30.0)
        errors.append("OVP 30 V must raise (never DP832 instrument max)")
    except ValueError:
        pass
    power_on_protected(psu, 1, 3.3, 0.05)
    psu_join = " ".join(str(w).upper() for w in psu.writes)
    if "PROT:STAT ON" not in psu_join:
        errors.append("power_on_protected must arm PROT:STAT ON")
    if "VOLT:PROT 6" not in psu_join and "VOLT:PROT 6.0" not in psu_join:
        if "VOLT:PROT" not in psu_join:
            errors.append("power_on_protected must write VOLT:PROT")

    dmm = sim.dmm
    dmm_setup_voltage(dmm)
    dmm_setup_current(dmm)
    dmm_join = " ".join(str(w).upper() for w in dmm.writes)
    if "*RST" in dmm_join:
        errors.append("DMM setup must not *RST (-113)")
    if any(tok in dmm_join for tok in ("NPLC", "AZER", "AVER", "TRAC", "HCOP")):
        errors.append("DMM setup must not send NPLC/AZER/AVER/TRAC/HCOP")
    from dmm_setup import dmm_write_ok, is_banned_dmm_scpi

    if not is_banned_dmm_scpi(":HCOP:SDUM:DATA?"):
        errors.append("is_banned_dmm_scpi must flag HCOP")
    n_dmm = len(dmm.writes)
    dmm_write_ok(dmm, "*RST")
    dmm_write_ok(dmm, ":SENS:CURR:NPLC 1")
    if len(dmm.writes) != n_dmm:
        errors.append("dmm_write_ok must skip *RST/NPLC (no -113 dialog)")
    skip_err = str(dmm.query("SYST:ERR?")).strip()
    if not skip_err.startswith("0"):
        errors.append(f"skip banned DMM header SYST:ERR want 0 got {skip_err!r}")

    stop_output(awg)
    power_off(psu)
    sim.reopen_bench()
    sim.reset_all()
    if any("*RST" in str(w).upper() for w in dmm.writes[-8:]):
        errors.append("reset_all must not *RST DMM")
    dmm.write("*RST")
    derr = str(dmm.query("SYST:ERR?")).strip()
    if not derr.startswith("-113"):
        errors.append(f"SIM DMM *RST must SYST:ERR -113 got {derr!r}")

    lb = loopback_check()
    bad = [c for c in (lb.get("checks") or []) if not c.get("ok")]
    if not lb.get("ok"):
        errors.append(f"loopback_check FAIL {[c.get('id') for c in bad]}")
    n_ok = sum(1 for c in (lb.get("checks") or []) if c.get("ok"))
    print(f"SIM load {load_s:.3f}s loopback {n_ok}/{len(lb.get('checks') or [])}")
    return errors


def _scan_live_banned_headers() -> list[str]:
    """Fail-closed: live helpers + ate/tests must not write AWG -116 / DMM -113."""
    from generator_setup import is_banned_awg_scpi
    from dmm_setup import is_banned_dmm_scpi

    errors: list[str] = []
    paths: list[Path] = [
        REPO_ROOT / "generator_setup.py",
        REPO_ROOT / "dmm_setup.py",
        REPO_ROOT / "psu_setup.py",
    ]
    for folder in (REPO_ROOT / "ate" / "tests", REPO_ROOT / "ate" / "drivers"):
        if folder.is_dir():
            paths.extend(sorted(folder.rglob("*.py")))
    for path in paths:
        try:
            rel = path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = path.name
        for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if ".write(" not in ln and ".query(" not in ln:
                continue
            probe = ln.replace("{ch}", "1").replace("{channel}", "1")
            if is_banned_awg_scpi(probe):
                errors.append(f"{rel}:{i} banned AWG header: {ln.strip()}")
            if path.name == "dmm_setup.py" or "dmm" in ln.lower():
                # Only flag actual write/query string literals, not is_banned checks.
                if ".write(" in ln or ".query(" in ln:
                    if is_banned_dmm_scpi(probe) and "is_banned_dmm_scpi" not in ln:
                        errors.append(f"{rel}:{i} banned DMM header: {ln.strip()}")
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(_scan_live_banned_headers())
    disc = REPO_ROOT / "ate" / "instruments" / "discovery.py"
    sess = REPO_ROOT / "ate" / "instruments" / "session.py"
    runner = REPO_ROOT / "ate" / "core" / "runner.py"
    db = REPO_ROOT / "ate" / "core" / "database.py"

    disc_src = disc.read_text(encoding="utf-8")
    sess_src = sess.read_text(encoding="utf-8")
    run_src = runner.read_text(encoding="utf-8")
    db_src = db.read_text(encoding="utf-8")

    if "def visa_resource_manager" not in disc_src:
        errors.append("discovery must expose visa_resource_manager")
    if "ASRL" not in disc_src or "skip_visa_resource" not in disc_src:
        errors.append("discovery must skip ASRL COM ports")
    if "mapping is not None" not in sess_src:
        errors.append("Instruments must not treat empty {} mapping as a new USB scan")
    if "self._mapping or None" in run_src:
        errors.append("open_session must pass mapping through, not `or None`")
    if "find_instruments(force=True)" not in run_src:
        errors.append("discover() must force-refresh the USB cache")
    if "if not mapped:" not in run_src:
        errors.append("open_session must force-rescan when Discover cache is empty")
    if 'if "MSO" not in mapped:' in run_src:
        errors.append("open_session must not force-rescan just because MSO is missing")
    if "def visa_inventory" not in disc_src:
        errors.append("discovery must expose visa_inventory (USB vs SIM, no power assume)")
    if "def bench_preflight" not in run_src:
        errors.append("runner must expose bench_preflight")
    if "loopback_check" not in run_src:
        errors.append("open_session(sim) must run loopback_check")
    if "self.gate.auto_continue = True" in run_src:
        errors.append("open_session(sim) must not set auto_continue; START would skip Continue")
    if "params.auto_continue" not in run_src:
        errors.append("run_sequence must take auto_continue from RunParams (DEMO only)")
    if "_idn_isolated" not in disc_src or "load_known_visa" not in disc_src:
        errors.append("discover live path must *IDN visa_known.yaml in a child")
    if "def probe_visa_urls" not in disc_src:
        errors.append("discover must probe only PnP OK yaml/extra URLs")
    if '"DG8" in u' in disc_src:
        errors.append("classify_idn must not treat USB serial DG8Q as AWG")
    if "usbtmc_pnp_ok_serials" not in disc_src or "taskkill" not in disc_src:
        errors.append("live *IDN must skip PnP Unknown and taskkill hung viOpen")
    if "def last_usb_map" not in disc_src or "def pnp_present" not in disc_src:
        errors.append("discovery must expose last_usb_map / pnp_present for header tiles")
    if "open_timeout=8000" not in sess_src:
        errors.append("open_resource must set open_timeout=8000 (ghost USBTMC)")
    if 'timeout_ms=20000 if key == "MSO" else 12000' not in sess_src:
        errors.append("MSO query timeout 20000 ms; PSU/AWG/DMM 12000 ms")
    if "_IDN_TIMEOUT_MS = 2000" not in disc_src:
        errors.append("live *IDN query timeout must be 2000 ms")
    if "open_timeout=5000" not in disc_src:
        errors.append("isolated *IDN open_timeout must be 5000 ms")
    if "find_instruments(rm=self.rm)" in sess_src:
        errors.append("Instruments must not list_resources via parent RM")
    if "def invalidate_tree_cache" not in db_src:
        errors.append("list_tree cache must be invalidatable after campaign writes")

    try:
        import pyvisa  # noqa: F401
    except Exception as exc:
        errors.append(f"pyvisa import failed: {exc}")

    from ate.instruments.discovery import (
        classify_idn,
        find_instruments,
        probe_visa_urls,
        skip_visa_resource,
        visa_url_from_pnp_instance,
    )

    if classify_idn("RIGOL TECHNOLOGIES,MSO5072,X,1.0") != "MSO":
        errors.append("classify_idn MSO5072")
    if classify_idn("RIGOL TECHNOLOGIES,DP832,X,1.0") != "PSU":
        errors.append("classify_idn DP832")
    if classify_idn("RIGOL TECHNOLOGIES,DG811,X,1.0") != "AWG":
        errors.append("classify_idn DG811")
    if classify_idn("KEITHLEY INSTRUMENTS,DMM6500,X,1.0") != "DMM":
        errors.append("classify_idn DMM6500")
    ghost_awg = "USB0::0x1AB1::0x0646::DG8Q281600755::INSTR"
    if classify_idn(ghost_awg) is not None:
        errors.append("classify_idn must not treat USB serial DG8Q as AWG")
    if classify_idn("USB0::0x1AB1::0x0E11::DP8C281601446::INSTR") is not None:
        errors.append("classify_idn must not treat PSU USB URL as PSU")
    live_psu = "USB0::0x1AB1::0x0E11::DP8C281601446::INSTR"
    known_probe = {"PSU": live_psu, "AWG": ghost_awg, "MSO": "USB0::0x1AB1::0x0515::MS5A281500878::INSTR"}
    probed = probe_visa_urls(known_probe, {"DP8C281601446"})
    if probed != [live_psu]:
        errors.append(f"probe_visa_urls must drop ghost AWG/MSO, got {probed}")
    if probe_visa_urls(known_probe, set()) != []:
        errors.append("probe_visa_urls must fail-closed when PnP OK is empty")
    extra_awg = "USB0::0x1AB1::0x0646::DG8Q281600757::INSTR"
    probed2 = probe_visa_urls(known_probe, {"DP8C281601446", "DG8Q281600757"}, [extra_awg])
    if live_psu not in probed2 or extra_awg not in probed2 or ghost_awg in probed2:
        errors.append(f"probe_visa_urls must add live extra AWG not yaml ghost, got {probed2}")
    pnp_url = visa_url_from_pnp_instance(r"USB\VID_1AB1&PID_0E11\DP8C281601446")
    if pnp_url != live_psu:
        errors.append(f"visa_url_from_pnp_instance {pnp_url}")
    if visa_url_from_pnp_instance(r"USB\VID_1AB1&PID_0515&MI_00\6&ABC&0&0000"):
        errors.append("composite Windows instance must not become a VISA URL")
    if not skip_visa_resource("ASRL3::INSTR"):
        errors.append("must skip ASRL")
    if not skip_visa_resource("USB0::0x1AB1::0x0514::SN::RAW"):
        errors.append("must skip USB RAW")
    if skip_visa_resource("USB0::0x1AB1::0x0514::SN::INSTR"):
        errors.append("must not skip USB INSTR")
    if skip_visa_resource("USB0::0x1AB1::0x0515::SN::INSTR"):
        errors.append("must not skip MSO5072 USB 0x0515")

    opened: list[str] = []

    class _FakeInst:
        timeout = 0

        def query(self, _cmd: str) -> str:
            return "RIGOL TECHNOLOGIES,MSO5072,FAKE,0.0"

        def close(self) -> None:
            return None

    class _FakeRM:
        def list_resources(self):
            return (
                "ASRL3::INSTR",
                "USB0::0x1AB1::0x0514::SN::RAW",
                "USB0::0x1AB1::0x0514::SN::INSTR",
            )

        def open_resource(self, res):
            opened.append(str(res))
            if skip_visa_resource(res):
                raise RuntimeError(f"must not open {res}")
            return _FakeInst()

    mapped = find_instruments(rm=_FakeRM(), force=True)
    if mapped.get("MSO") != "USB0::0x1AB1::0x0514::SN::INSTR":
        errors.append(f"fake discover map {mapped}")
    if any("ASRL" in r.upper() or "::RAW" in r.upper() for r in opened):
        errors.append(f"opened skipped resources: {opened}")

    from ate.instruments.session import Instruments

    if tuple(Instruments.REQUIRED_AT_OPEN) != ():
        errors.append("REQUIRED_AT_OPEN must be empty so USB opens without MSO")
    reset_fn = next(
        (
            n
            for n in ast.walk(ast.parse(sess_src))
            if isinstance(n, ast.FunctionDef) and n.name == "reset_all"
        ),
        None,
    )
    if reset_fn is None:
        errors.append("session.reset_all missing")
    elif "self.dmm" in ast.unparse(reset_fn):
        errors.append("reset_all must not *RST DMM6500")

    sim = Instruments.simulated()
    if not getattr(sim, "_simulated", False):
        errors.append("simulated() must set _simulated")
    if sim.rm is not None:
        errors.append("SIM session must not create a PyVISA ResourceManager")
    if "self.dmm" not in sess_src:
        errors.append("Instruments must set self.dmm")
    if getattr(sim, "dmm", None) is None:
        errors.append("simulated() must expose dmm")

    run_tree = ast.parse(run_src)
    for node in ast.walk(run_tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run_sequence":
            for child in ast.walk(node):
                if isinstance(child, ast.ImportFrom):
                    names = [a.name for a in child.names]
                    if "get_context" in names:
                        errors.append("run_sequence must not re-import get_context")

    backend = "none"
    try:
        from ate.instruments.discovery import load_known_visa

        known = load_known_visa()
        for kind in ("PSU", "AWG", "DMM", "MSO"):
            if kind not in known:
                errors.append(f"visa_known.yaml must list {kind} URL")
    except Exception as exc:
        errors.append(f"visa_known.yaml failed: {exc}")

    errors.extend(_sim_load_timing_and_control())

    if errors:
        print("FAIL check_visa:")
        for e in errors:
            print(f"  - {e}")
        return 1
    from ate.instruments.discovery import visa_inventory
    import time as _time

    t_inv = _time.perf_counter()
    inv = visa_inventory(force=True)
    inv_s = _time.perf_counter() - t_inv
    backend = str(inv.get("backend") or "none")
    print(f"visa_inventory {inv_s:.2f}s backend={backend}")
    if inv_s > 90.0:
        print("FAIL check_visa:")
        print(f"  - visa_inventory hung {inv_s:.1f}s (open_timeout/taskkill should bound *IDN)")
        return 1
    print(
        f"preflight mode={inv.get('mode')} reason={inv.get('reason')} "
        f"keep={inv.get('keep')} skip={inv.get('skip')} map={inv.get('mapping')}"
    )
    print(
        f"OK check_visa: known *IDN isolated (no list_resources); "
        f"backend={backend}; ASRL/RAW skip; empty mapping not a rescan; SIM has no RM"
    )
    mapping = inv.get("mapping") or {}
    if "MSO" not in mapping:
        print("USB MSO *IDN missed. Plug MSO5072 KEEP URL, close Ultra Sigma, unplug ghost USBTMC.")
    if not mapping:
        print("USB *IDN none. Plug PSU/AWG/DMM/MSO, close Ultra Sigma.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
