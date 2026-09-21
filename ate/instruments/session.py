"""Instrument session -- PSU/AWG/DMM/MSO optional at open; tests gate missing gear."""
from __future__ import annotations

from typing import Optional

from ate.instruments.discovery import (
    find_instruments,
    visa_backend_name,
    visa_resource_manager,
)


class Instruments:
    REQUIRED_AT_OPEN = ()

    def __init__(self, mapping: Optional[dict[str, str]] = None) -> None:
        self._simulated = False
        self.rm = visa_resource_manager()
        # Empty {} means already scanned -- do not treat it as "scan again".
        # mapping=None uses visa_known.yaml *IDN (never list_resources on this PC).
        self.inst_map = dict(mapping) if mapping is not None else find_instruments()
        print("Final Mapping:")
        print(self.inst_map)

        missing = [k for k in self.REQUIRED_AT_OPEN if k not in self.inst_map]
        if missing:
            raise RuntimeError(
                f"Required instrument(s) not found: {missing}. "
                f"VISA {visa_backend_name()}. "
                "Close Ultra Sigma, plug MSO USB, Discover. No USB: Open SIM."
            )

        self.scope = self._open("MSO", required=False)
        self.psu = self._open("PSU", required=False)
        self.gen = self._open("AWG", required=False)
        self.dmm = self._open("DMM", required=False)
        if self.dmm is not None:
            try:
                from dmm_setup import dmm_dismiss_header

                dmm_dismiss_header(self.dmm)
            except Exception as exc:
                print(f"DMM drain at open: {exc}", flush=True)
        for key, handle in (
            ("PSU", self.psu),
            ("AWG", self.gen),
            ("DMM", self.dmm),
            ("MSO", self.scope),
        ):
            if handle is None:
                print(f"{key} not connected -- session open without it.")

    @property
    def awg(self):
        """Alias: VISA session stores AWG as .gen. Recipe walker / tests may say .awg."""
        return self.gen

    @property
    def mso(self):
        """Alias: VISA session stores MSO as .scope."""
        return self.scope

    @classmethod
    def simulated(cls) -> "Instruments":
        """No USB. Fake SCPI for DEMO / disconnected START."""
        from ate.instruments.sim import SIM_MAP, SimResource, reset_bus

        reset_bus()
        obj = cls.__new__(cls)
        obj._simulated = True
        obj.rm = None
        obj.inst_map = dict(SIM_MAP)
        obj.scope = SimResource("MSO")
        obj.psu = SimResource("PSU")
        obj.gen = SimResource("AWG")
        obj.dmm = SimResource("DMM")
        print("Final Mapping:")
        print(obj.inst_map)
        print("SIM session -- no USB; PSU/AWG/DMM/MSO are fake SCPI")
        return obj

    def available_devices(self) -> set[str]:
        return set(self.inst_map.keys())

    def _open_url(self, url: str, *, timeout_ms: int):
        """open_timeout so a ghost USBTMC cannot block Open Session forever."""
        inst = self.rm.open_resource(url, open_timeout=8000)
        inst.timeout = timeout_ms
        return inst

    def _open(self, key: str, required: bool = True):
        url = self.inst_map.get(key)
        if not url:
            if required:
                raise RuntimeError(f"{key} not found")
            return None
        # MSO :DISP:DATA? / MEAS / AUToscale need >3s. TMO was aborting live slew.
        return self._open_url(url, timeout_ms=20000 if key == "MSO" else 12000)

    def reopen_bench(self) -> None:
        """Drop poisoned PSU/AWG/DMM handles. Idle PSU. Do not touch MSO."""
        from psu_setup import power_off

        if getattr(self, "_simulated", False):
            return
        for key, attr in (("PSU", "psu"), ("AWG", "gen"), ("DMM", "dmm")):
            inst = getattr(self, attr, None)
            if inst is not None:
                try:
                    inst.close()
                except Exception:
                    pass
                setattr(self, attr, None)
            url = self.inst_map.get(key)
            if not url or self.rm is None:
                continue
            handle = self._open_url(url, timeout_ms=12000)
            setattr(self, attr, handle)
        if self.psu is not None:
            try:
                power_off(self.psu)
            except Exception as exc:
                print(f"reopen_bench power_off: {exc}")

    def reopen_scope(self):
        """Drop a poisoned MSO VISA handle and open a fresh one."""
        if getattr(self, "_simulated", False):
            from ate.instruments.sim import SimResource

            self.scope = SimResource("MSO")
            self.scope.timeout = 5000
            return self.scope
        url = self.inst_map.get("MSO")
        if not url:
            raise RuntimeError("MSO not in mapping")
        if self.scope is not None:
            try:
                self.scope.close()
            except Exception:
                pass
        self.scope = self._open_url(url, timeout_ms=20000)
        return self.scope

    def reset_all(self) -> None:
        # DMM6500 *RST -> SYST:ERR -113; dmm_setup sets FUNC instead.
        for inst in (self.scope, self.gen, self.psu):
            if inst is None:
                continue
            try:
                inst.write("*RST")
            except Exception as exc:
                print(f"Reset failed: {exc}")

    def close_all(self) -> None:
        for inst in (self.scope, self.gen, self.psu, self.dmm):
            if inst is None:
                continue
            try:
                inst.close()
            except Exception:
                pass
