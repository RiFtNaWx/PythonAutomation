"""VISA discovery -- MSO / PSU / AWG / DMM.

DMM is optional at session open (same as PSU/AWG). Logic IDD/VOUT/cap_load and
OpAmp VOL require it at run time.
"""
from __future__ import annotations

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


def classify_idn(idn: str) -> str | None:
    """Return MSO / PSU / AWG / DMM or None from a *IDN? string."""
    u = (idn or "").upper()
    if "MSO5" in u:
        return "MSO"
    if "DP832" in u or ",DP8" in u:
        return "PSU"
    if "DG811" in u or "DG8" in u:
        return "AWG"
    if any(tok in u for tok in _DMM_MODEL):
        return "DMM"
    if "KEITHLEY" in u and any(
        tok in u for tok in ("DMM", "2000", "2100", "2110", "2010")
    ):
        return "DMM"
    if "KEYSIGHT" in u and "344" in u:
        return "DMM"
    return None


def find_instruments() -> dict[str, str]:
    import pyvisa

    rm = pyvisa.ResourceManager()
    resources = rm.list_resources()
    instruments: dict[str, str] = {}

    for res in resources:
        # Skip COM/ASRL -- they hang on *IDN? and are never our bench gear
        if str(res).upper().startswith("ASRL"):
            continue
        try:
            inst = rm.open_resource(res)
            inst.timeout = 3000
            idn = inst.query("*IDN?").strip()
            print(f"Found: {res} -> {idn}")
            kind = classify_idn(idn)
            if kind and kind not in instruments:
                instruments[kind] = res
            inst.close()
        except Exception as exc:
            print(f"Skipping {res}: {exc}")
    return instruments
