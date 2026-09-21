"""Thin wrapper. Prefer python -m ate.core.ingest_datasheet <part>."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("pdf", type=Path)
    p.add_argument("--part", required=True)
    p.add_argument("--engine", default="auto")
    p.add_argument("--i-named-this", action="store_true")
    args = p.parse_args()
    from ate.core.ocr_engine import extract_pdf

    got = extract_pdf(args.pdf, engine=args.engine, named_cloud=args.i_named_this)
    print(json.dumps({"part": args.part, **got, "write": "none -- run ingest_datasheet"}, indent=2)[:12000])
    print("Is it like this? Affirm then python -m ate.core.ingest_datasheet", args.part, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
