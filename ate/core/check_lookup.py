"""Self-check: local datasheet lookup + limits yaml for inventory parts.

Run: python -m ate.core.check_lookup
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    errors: list[str] = []
    from ate.core.lookup import (
        INDEX_PATH,
        build_index,
        reference_root,
        resolve_pdf,
        sync_limits_from_local,
    )
    from ate.core.specs import LIMITS_DIR, load_part_specs

    root = reference_root()
    if not root.is_dir():
        errors.append(f"reference_root missing: {root}")
        print("FAIL check_lookup:")
        for e in errors:
            print(f"  - {e}")
        return 1

    idx = build_index(persist=True)
    if not INDEX_PATH.is_file():
        errors.append("datasheets.yaml not written")
    pdfs = idx.get("pdfs") or []
    if not any("RS1G08" in (r.get("file") or "") for r in pdfs):
        errors.append("index missing RS1G08 pdf")
    p = resolve_pdf("RS1G08", index=idx)
    if p is None or not Path(p).is_file():
        errors.append("resolve_pdf RS1G08 failed")
    p62 = resolve_pdf("RS622", index=idx)
    if p62 is None or not Path(p62).is_file():
        errors.append("resolve_pdf RS622 (family RS62X) failed")
    if p62 is not None and "RS62X" not in Path(p62).name:
        errors.append(f"RS622 should use RS62X family PDF, got {p62}")
    p2323 = resolve_pdf("RS2323", index=idx)
    if p2323 is not None and "RS22X" in Path(p2323).name:
        errors.append("RS2323 must not use RS222 opamp family PDF")
    p3213 = resolve_pdf("RS3213", index=idx)
    if p3213 is not None and "RS32X" in Path(p3213).name:
        errors.append("RS3213 LDO must not use RS321/RS358 opamp family PDF")
    local_2323 = list(root.glob("RS2323*.pdf"))
    if not local_2323:
        errors.append("RS2323 English PDF missing from local Reference")
    if local_2323 and (p2323 is None or not Path(p2323).is_file()):
        errors.append("RS2323 PDF is in Reference but resolve_pdf missed it")
    if p2323 is not None and Path(p2323).is_file() and "RS22X" in Path(p2323).name:
        errors.append("RS2323 must not use RS222 opamp family PDF")
    local_3213 = list(root.glob("RS3213*.pdf"))
    if local_3213 and p3213 is not None and "RS32X" in Path(p3213).name:
        errors.append("RS3213 LDO must not use RS321/RS358 opamp family PDF")
    iq = next((s for s in load_part_specs("rs3213") if s.get("id") == "IQ_uA"), {})
    if iq.get("typ") != 30:
        errors.append(f"rs3213 IQ_uA typ 30 from English PDF missing, got {iq}")
    specs0204 = load_part_specs("rs0204")
    if not any(s.get("id") == "ICC_uA" and s.get("max") == 10 for s in specs0204):
        errors.append("rs0204 ICC_uA max 10 uA from local PDF table missing")

    sync_limits_from_local("RS1G08", part_key="rs1g08", web_ok=False)
    specs = load_part_specs("rs1g08")
    if not any(s.get("id", "").startswith("VOH_") for s in specs):
        errors.append("rs1g08 limits missing VOH from part yaml table")
    ext = Path(__file__).resolve().parents[1] / "config" / "datasheets" / "text" / "rs1g08.txt"
    if not ext.is_file():
        errors.append("rs1g08 extract missing after sync")
    else:
        blob = ext.read_text(encoding="utf-8")
        if "VOH" not in blob:
            errors.append("rs1g08 extract must contain VOH (glyph-join PDF text)")
        if "IOH = -32mA 4.5V 3.8" not in blob:
            errors.append("rs1g08 extract must keep 8.4/9.2 VOH 4.5V min 3.8")
    ext2323 = Path(__file__).resolve().parents[1] / "config" / "datasheets" / "text" / "rs2323.txt"
    if ext2323.is_file() and "ON-State Resistance" not in ext2323.read_text(encoding="utf-8"):
        errors.append("rs2323 extract must contain ON-State Resistance banner")
    sync_limits_from_local("RS1G32", part_key="rs1g32", web_ok=False)
    specs32 = load_part_specs("rs1g32")
    if not any(str(s.get("id") or "").startswith("VOH_") for s in specs32):
        errors.append("rs1g32 limits missing VOH from part yaml table")
    sync_limits_from_local("RS1G07", part_key="rs1g07", web_ok=False)
    icc = next((s for s in load_part_specs("rs1g07") if s.get("id") == "ICC_uA"), {})
    if icc.get("max") != 1:
        errors.append(f"rs1g07 ICC_uA max 1 uA from local PDF missing, got {icc}")
    if not (LIMITS_DIR / "rs622.yaml").is_file():
        errors.append("rs622 limits yaml missing")
    vos = next((s for s in load_part_specs("rs622") if s.get("id") == "VOS_mV"), {})
    if vos.get("max") != 3.0:
        errors.append("rs622 VOS max must stay 3 after local sync")

    if errors:
        print("FAIL check_lookup:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK check_lookup pdfs={len(pdfs)} index={INDEX_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
