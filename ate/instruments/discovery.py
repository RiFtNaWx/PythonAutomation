"""VISA discovery -- MSO / PSU / AWG / DMM.

DMM is optional at session open (same as PSU/AWG). Logic IDD/VOUT/cap_load and
OpAmp VOL require it at run time.
"""
from __future__ import annotations

import re
import time
from typing import Any

_DMM_MODEL = (
    "DMM6500",
    "DMM7510",
    "34461A",
    "34401A",
    "34410A",
    "34411A",
    "34465A",
    "34470A",
    "34420A",
)

_RM = None
_BACKEND = "none"
_CACHE: dict[str, Any] = {"t": 0.0, "map": {}, "scanned": False}
CACHE_S = 15.0
_IDN_TIMEOUT_MS = 2000
_KNOWN_ORDER = ("PSU", "AWG", "DMM", "MSO")


def visa_backend_name() -> str:
    return _BACKEND


def visa_resource_manager():
    """One shared PyVISA RM: default NI/IVI, then @ivi, then pyvisa-py (@py)."""
    global _RM, _BACKEND
    if _RM is not None:
        return _RM
    import pyvisa

    errors: list[str] = []
    for spec in (None, "@ivi", "@py"):
        label = spec or "default"
        try:
            rm = pyvisa.ResourceManager() if spec is None else pyvisa.ResourceManager(spec)
            visalib = getattr(rm, "visalib", None)
            lib_name = type(visalib).__name__ if visalib is not None else type(rm).__name__
            _RM = rm
            _BACKEND = f"{lib_name}:{label}"
            print(f"PyVISA backend {_BACKEND}")
            return rm
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    raise RuntimeError(
        "PyVISA has no backend. Install NI-VISA (bench USB) or pip install pyvisa-py. "
        "No instruments: Open SIM. "
        + " | ".join(errors)
    )


def skip_visa_resource(res: str) -> bool:
    """COM ports hang on *IDN?; RAW USB is not SCPI. Do not skip MSO 0x0515."""
    u = str(res or "").upper()
    if u.startswith("ASRL"):
        return True
    if "::RAW" in u:
        return True
    return False


def visa_serial(res: str) -> str:
    parts = [p for p in str(res or "").split("::") if p]
    return parts[3].upper() if len(parts) >= 4 else ""


_VIDPID_RE = re.compile(r"VID_([0-9A-F]{4}).*PID_([0-9A-F]{4})", re.I)


def visa_url_from_pnp_instance(instance_id: str) -> str | None:
    """USB\\VID_xxxx&PID_yyyy\\SERIAL -> USB0::0xVID::0xPID::SERIAL::INSTR."""
    raw = str(instance_id or "").strip()
    if not raw:
        return None
    parts = [p for p in raw.replace("/", "\\").split("\\") if p]
    vid = pid = ""
    for p in parts:
        m = _VIDPID_RE.search(p)
        if m:
            vid, pid = m.group(1).upper(), m.group(2).upper()
    serial = parts[-1] if parts else ""
    if not vid or not pid or not serial or "&" in serial:
        return None
    if serial.upper().startswith(("USB", "VID_")):
        return None
    return f"USB0::0x{vid}::0x{pid}::{serial}::INSTR"


_PNP_IDS: dict[str, Any] = {"t": 0.0, "ids": None}


def _pnp_ok_instance_ids() -> list[str]:
    """Windows USBTMC Status=OK InstanceIds. Empty on failure (fail-closed)."""
    import subprocess

    now = time.monotonic()
    cached = _PNP_IDS.get("ids")
    if cached is not None and (now - float(_PNP_IDS["t"])) < 8.0:
        return list(cached)

    ps = (
        "Get-PnpDevice | Where-Object { $_.Class -eq 'USBTestAndMeasurementDevice' "
        "-and $_.Status -eq 'OK' } | ForEach-Object { $_.InstanceId }"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            timeout=8,
            capture_output=True,
            text=True,
        )
    except Exception:
        ids: list[str] = []
        _PNP_IDS["t"] = time.monotonic()
        _PNP_IDS["ids"] = ids
        return ids
    ids = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()]
    _PNP_IDS["t"] = time.monotonic()
    _PNP_IDS["ids"] = ids
    return ids


def usbtmc_pnp_ok_serials() -> set[str]:
    """Windows USBTMC Status=OK serials. Ghost Unknown rows hang NI viOpen."""
    out: set[str] = set()
    for inst in _pnp_ok_instance_ids():
        parts = [p for p in inst.replace("/", "\\").split("\\") if p]
        if parts:
            out.add(parts[-1].upper())
        url = visa_url_from_pnp_instance(inst)
        sn = visa_serial(url or "")
        if sn:
            out.add(sn)
    return out


def usbtmc_pnp_ok_urls() -> list[str]:
    """VISA INSTR URLs for PnP OK USBTMC. Skips composite Windows instance ids."""
    out: list[str] = []
    seen: set[str] = set()
    for inst in _pnp_ok_instance_ids():
        url = visa_url_from_pnp_instance(inst)
        if not url:
            continue
        key = url.upper()
        if key not in seen:
            seen.add(key)
            out.append(url)
    return out


def probe_visa_urls(
    known: dict[str, str],
    ok_sn: set[str],
    extra_urls: list[str] | None = None,
) -> list[str]:
    """yaml + PnP OK URLs to *IDN. Empty ok_sn: probe nothing (ghosts hang NI)."""
    if not ok_sn:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for kind in _KNOWN_ORDER:
        res = str(known.get(kind) or "").strip()
        if not res or skip_visa_resource(res):
            continue
        sn = visa_serial(res)
        if not sn or sn not in ok_sn:
            continue
        key = res.upper()
        if key not in seen:
            seen.add(key)
            out.append(res)
    for res in extra_urls or []:
        res = str(res or "").strip()
        if not res or skip_visa_resource(res):
            continue
        sn = visa_serial(res)
        if sn and sn not in ok_sn:
            continue
        key = res.upper()
        if key not in seen:
            seen.add(key)
            out.append(res)
    return out


def load_known_visa() -> dict[str, str]:
    """Bench USBTMC URLs. Avoids NI list_resources hanging on ghost devices."""
    from ate.core.paths import CONFIG_DIR
    import yaml

    path = CONFIG_DIR / "visa_known.yaml"
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw = data.get("instruments") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for kind in _KNOWN_ORDER:
        url = str(raw.get(kind) or "").strip()
        if url:
            out[kind] = url
    return out


def _idn_isolated(res: str, timeout_s: float = 12.0) -> tuple[str | None, str]:
    """Known-URL *IDN in a child. taskkill /T if NI viOpen ignores timeout."""
    import subprocess
    import sys

    code = (
        "import sys,pyvisa\n"
        "res=sys.argv[1]\n"
        "rm=pyvisa.ResourceManager()\n"
        "inst=rm.open_resource(res, open_timeout=5000)\n"
        "inst.timeout=2000\n"
        "print(inst.query('*IDN?').strip())\n"
        "inst.close()\n"
    )
    flags = 0
    if sys.platform == "win32":
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    proc = subprocess.Popen(
        [sys.executable, "-c", code, res],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=flags,
    )
    try:
        out, err = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
            text=True,
        )
        try:
            proc.communicate(timeout=3)
        except Exception:
            pass
        print(f"Skipping {res}: *IDN timeout {timeout_s}s")
        return None, "timeout"
    if proc.returncode != 0:
        err = (err or out or "idn fail").strip()
        print(f"Skipping {res}: {err.splitlines()[-1] if err else 'idn fail'}")
        return None, err
    idn = (out or "").strip().splitlines()[-1] if out else ""
    print(f"Found: {res} -> {idn}")
    return classify_idn(idn), idn


def _idn_open(rm, res: str) -> tuple[str | None, str]:
    """Fake-RM / scan path. Live known URLs use _idn_isolated instead."""
    inst = None
    try:
        inst = rm.open_resource(res)
        inst.timeout = _IDN_TIMEOUT_MS
        idn = inst.query("*IDN?").strip()
        print(f"Found: {res} -> {idn}")
        return classify_idn(idn), idn
    except Exception as exc:
        print(f"Skipping {res}: {exc}")
        return None, str(exc)
    finally:
        if inst is not None:
            try:
                inst.close()
            except Exception:
                pass


def classify_idn(idn: str) -> str | None:
    """Return MSO / PSU / AWG / DMM from a *IDN? string. Never a VISA URL."""
    u = (idn or "").strip().upper()
    if not u:
        return None
    if u.startswith(("USB", "TCPIP", "GPIB", "ASRL", "HISLIP", "VXI")):
        return None
    fields = [p.strip() for p in u.split(",")]
    model = fields[1] if len(fields) > 1 else fields[0]
    if "MSO5" in model:
        return "MSO"
    if "DP832" in model or model.startswith("DP8"):
        return "PSU"
    if model.startswith("DG8"):
        return "AWG"
    if any(tok in model for tok in _DMM_MODEL) or any(tok in u for tok in _DMM_MODEL):
        return "DMM"
    if "KEITHLEY" in u and any(
        tok in u for tok in ("DMM", "2000", "2100", "2110", "2010")
    ):
        return "DMM"
    if "KEYSIGHT" in u and "344" in u:
        return "DMM"
    return None


def clear_discover_cache() -> None:
    _CACHE["t"] = 0.0
    _CACHE["map"] = {}
    _CACHE["scanned"] = False


def find_instruments(*, rm=None, force: bool = False) -> dict[str, str]:
    now = time.monotonic()
    use_cache = rm is None
    if (
        use_cache
        and not force
        and _CACHE["scanned"]
        and (now - float(_CACHE["t"])) < CACHE_S
    ):
        return dict(_CACHE["map"])

    instruments: dict[str, str] = {}
    if use_cache:
        known = load_known_visa()
        if known:
            ok_sn = usbtmc_pnp_ok_serials()
            extra = usbtmc_pnp_ok_urls()
            yaml_by_url = {str(u).upper(): k for k, u in known.items() if u}
            for res in probe_visa_urls(known, ok_sn, extra):
                got, _idn = _idn_isolated(res)
                expect = yaml_by_url.get(res.upper())
                if expect and got and got != expect:
                    print(f"Skipping {res}: yaml {expect} *IDN classified {got}")
                    continue
                if got and got not in instruments:
                    instruments[got] = res
            skipped = [
                u
                for k, u in known.items()
                if u and u not in instruments.values()
            ]
            if skipped:
                print(f"Discover skipped (no *IDN / PnP Unknown): {skipped}")
            _CACHE["t"] = time.monotonic()
            _CACHE["map"] = dict(instruments)
            _CACHE["scanned"] = True
            return instruments

    rm = rm or visa_resource_manager()
    try:
        resources = rm.list_resources()
    except Exception as exc:
        raise RuntimeError(
            f"PyVISA list_resources failed ({visa_backend_name()}): {exc}. "
            "Close Ultra Sigma. No USB: Open SIM."
        ) from exc

    for res in resources:
        if skip_visa_resource(res):
            continue
        kind, _idn = _idn_open(rm, res)
        if kind and kind not in instruments:
            instruments[kind] = res

    if not instruments:
        print(
            f"Discover empty ({visa_backend_name()}): "
            f"{len(resources)} VISA resource(s); ASRL/RAW skipped; none classified MSO/PSU/AWG/DMM"
        )
    if use_cache:
        _CACHE["t"] = time.monotonic()
        _CACHE["map"] = dict(instruments)
        _CACHE["scanned"] = True
    return instruments


def visa_inventory(*, force: bool = True) -> dict[str, Any]:
    """KEEP = *IDN mapping only. yaml/PnP ghosts go in skip. No list_resources."""
    skip: list[str] = []
    keep: list[str] = []
    mapping: dict[str, str] = {}
    backend = "none"
    error = ""
    known: dict[str, str] = {}
    try:
        known = load_known_visa()
        yaml_urls = [known[k] for k in _KNOWN_ORDER if known.get(k)]
        mapping = find_instruments(force=force)
        keep = [mapping[k] for k in _KNOWN_ORDER if mapping.get(k)]
        keep_set = {u.upper() for u in keep}
        skip = [u for u in yaml_urls if u.upper() not in keep_set]
        backend = visa_backend_name() if mapping else "none"
    except Exception as exc:
        error = str(exc)
    mode = "usb" if mapping else "sim"
    reason = (
        f"USB *IDN {sorted(mapping)}"
        if mode == "usb"
        else (
            error
            or (
                "PnP OK / yaml USB present but no *IDN (unpowered, Unknown, or busy)"
                if known
                else "no known USB URLs"
            )
        )
    )
    return {
        "backend": backend,
        "keep": keep,
        "skip": skip,
        "mapping": dict(mapping),
        "mode": mode,
        "reason": reason,
        "error": error,
        "powered_output": False,
    }
