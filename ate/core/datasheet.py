"""Fetch English RUN-IC product page + PDF link for one part we already test.

Writes ate/config/limits/<key>.yaml only. Filled min/max stay.
Never dumps the website catalog into #Test_Database.
"""
from __future__ import annotations

import re
from html import unescape
from typing import Any
from urllib.parse import urljoin, urlparse

import yaml

from ate.core.paths import PARTS_DIR
from ate.core.specs import LIMITS_DIR, load_part_yaml

EN_ORIGIN = "https://en.run-ic.com"
WWW_EN = "https://www.run-ic.com/en"
_ALLOWED_HOSTS = frozenset({"en.run-ic.com", "www.run-ic.com"})
_PART_RE = re.compile(r"^RS[0-9A-Z\-]+$", re.I)
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
_PDF_RE = re.compile(
    r"https?://(?:en\.|www\.)run-ic\.com(?:/en)?/upload/goods/[^\s\"']+\.pdf",
    re.I,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _norm_part(raw: str) -> str:
    p = re.sub(r"[^A-Za-z0-9\-]+", "", str(raw or "").upper())
    if not _PART_RE.match(p):
        raise ValueError("part must look like RS622 (inventory SKU, not a catalog scrape)")
    return p


def _get(url: str) -> str:
    import requests

    host = urlparse(url).hostname or ""
    if host not in _ALLOWED_HOSTS:
        raise ValueError("only en.run-ic.com / www.run-ic.com")
    r = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "ATE-console/1.0 (lab datasheet limits; one SKU)"},
    )
    r.raise_for_status()
    return r.text


def _text(html: str) -> str:
    t = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    t = re.sub(r"(?is)<style.*?>.*?</style>", " ", t)
    t = _TAG_RE.sub(" ", t)
    t = unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def _search_hits(part: str) -> list[str]:
    """Product detail URLs for one SKU. Skip category /goods/N.html nav."""
    sku = str(part or "").lower()
    urls: list[str] = []
    for search in (
        f"{WWW_EN}/search.html?keyword={part}",
        f"{EN_ORIGIN}/search.html?keyword={part}",
    ):
        try:
            html = _get(search)
        except Exception:
            continue
        near: list[str] = []
        other: list[str] = []
        for m in _HREF_RE.finditer(html):
            abs_u = urljoin(search, m.group(1))
            host = urlparse(abs_u).hostname or ""
            if host not in _ALLOWED_HOSTS:
                continue
            path = urlparse(abs_u).path.lower()
            if re.search(r"/goods/\d+\.html$", path):
                continue
            if "/details/" not in path and "/goods/" not in path:
                continue
            window = html[max(0, m.start() - 240) : m.end() + 240].lower()
            if abs_u in near or abs_u in other or abs_u in urls:
                continue
            if sku in window or sku in abs_u.lower():
                near.append(abs_u)
            elif "/details/" in path:
                other.append(abs_u)
        for u in near + other:
            if u not in urls:
                urls.append(u)
    return urls[:8]


def _inventory_category(part: str) -> str:
    try:
        from ate.core.new_product import load_inventory

        sku = str(part or "").upper()
        for row in load_inventory():
            if str(row.get("part") or "").upper() == sku:
                return str(row.get("category") or "").strip().lower()
    except Exception:
        pass
    return ""


def _guess_specs(text: str, part: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    t = text
    cat = _inventory_category(part)
    opamp_ok = cat not in ("analog_switch", "power", "logic", "level")

    def add(sid: str, **kw: Any) -> None:
        row = {"id": sid, "source": f"en.run-ic.com {part}"}
        row.update(kw)
        out.append(row)

    if not opamp_ok:
        m = re.search(r"(?:I\+|quiescent current|supply current)[^\.]{0,60}?([0-9.]+)\s*uA", t, re.I)
        if m and cat == "analog_switch":
            add("IPLUS_uA", unit="uA", max=float(m.group(1)), test="iplus")
        m = re.search(r"(?:output voltage|VOUT)[^\.]{0,40}?([0-9.]+)\s*V", t, re.I)
        if m and cat == "power":
            add("VOUT_V", unit="V", typ=float(m.group(1)), test="iq")
        m = re.search(r"(?:Low IQ|quiescent current|\bIQ\b)[^\.]{0,50}?([0-9.]+)\s*[uµμ]A", t, re.I)
        if m and cat == "power":
            add("IQ_uA", unit="uA", typ=float(m.group(1)), test="iq")
        m = re.search(
            r"Low Power Consumption:\s*([0-9.]+)\s*[uµμ]A\s*\(\s*Max\s*\)",
            t,
            re.I,
        )
        if m and cat in ("logic", "level"):
            add("ICC_uA", unit="uA", max=float(m.group(1)), test="supply_current")
        m = re.search(r"supply[^\.]{0,30}?([0-9.]+)\s*V\s*(?:~|-|to)\s*([0-9.]+)\s*V", t, re.I)
        if not m:
            m = re.search(
                r"Operating Voltage Range:\s*([0-9.]+)\s*V\s*to\s*([0-9.]+)\s*V",
                t,
                re.I,
            )
        if m:
            add("VCC_V", unit="V", min=float(m.group(1)), max=float(m.group(2)))
        m = re.search(r"ON-State Resistance,\s*([0-9.]+)", t, re.I)
        if m and cat == "analog_switch":
            add("RON_ohm", unit="ohm", typ=float(m.group(1)))
        return out

    m = re.search(r"(?:Vos|offset voltage)[^\.]{0,80}?([0-9.]+)\s*mV\s*typical[^\.]{0,40}?([0-9.]+)\s*mV\s*max", t, re.I)
    if m:
        add("VOS_mV", unit="mV", typ=float(m.group(1)), max=float(m.group(2)), test="vos_sweep")
    else:
        m = re.search(r"([0-9.]+)\s*mV\s*typical.{0,20}([0-9.]+)\s*mVmax", t, re.I)
        if m:
            add("VOS_mV", unit="mV", typ=float(m.group(1)), max=float(m.group(2)), test="vos_sweep")
        else:
            m = re.search(r"([0-9.]+)\s*mV\s*Typical\s*Vos", t, re.I)
            if m:
                add("VOS_mV", unit="mV", typ=float(m.group(1)), test="vos_sweep")
    m = re.search(r"(?:Gain Bandwidth|GBW)[^\.]{0,40}?([0-9.]+)\s*MHz", t, re.I)
    if m:
        add("GBW_MHz", unit="MHz", typ=float(m.group(1)), test="gbw")
    m = re.search(r"slew rate[^\.]{0,40}?([0-9.]+)\s*V\s*/\s*u?s", t, re.I)
    if m:
        add("SR_Vus", unit="V/us", typ=float(m.group(1)), test="slew")
    m = re.search(r"(?:quiescent current|Iq)[^\.]{0,40}?([0-9.]+)\s*uA", t, re.I)
    if m:
        add("IQ_uA", unit="uA", typ=float(m.group(1)))
    m = re.search(r"supply[^\.]{0,30}?([0-9.]+)\s*V\s*(?:~|-|to)\s*([0-9.]+)\s*V", t, re.I)
    if m:
        add("VCC_V", unit="V", min=float(m.group(1)), max=float(m.group(2)))
    return out


def _merge_specs(existing: list[Any], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in existing:
        if isinstance(row, dict) and row.get("id"):
            by_id[str(row["id"])] = dict(row)
    for row in incoming:
        sid = str(row.get("id") or "")
        if not sid:
            continue
        cur = by_id.get(sid, {"id": sid})
        for key in ("unit", "min", "max", "typ", "test", "source"):
            if cur.get(key) in (None, "") and row.get(key) not in (None, ""):
                cur[key] = row[key]
        by_id[sid] = cur
    return list(by_id.values())


def _pdf_urls(html: str, page_url: str = "") -> list[str]:
    urls: list[str] = []
    base = page_url or (EN_ORIGIN + "/")
    for u in _PDF_RE.findall(html):
        if u not in urls:
            urls.append(u)
    for href in _HREF_RE.findall(html):
        abs_u = urljoin(base, href)
        host = urlparse(abs_u).hostname or ""
        if host not in _ALLOWED_HOSTS:
            continue
        if abs_u.lower().endswith(".pdf") and abs_u not in urls:
            urls.append(abs_u)
    return urls


def _download_pdf(url: str) -> bytes:
    import requests

    host = urlparse(url).hostname or ""
    if host not in _ALLOWED_HOSTS:
        raise ValueError("only en.run-ic.com PDF")
    r = requests.get(
        url,
        timeout=40,
        headers={"User-Agent": "ATE-console/1.0 (lab datasheet; one SKU)"},
    )
    r.raise_for_status()
    return r.content


def _store_reference_pdf(sku: str, url: str, content: bytes) -> "Path":
    from pathlib import Path

    from ate.core.lookup import _PART_FILE, reference_root

    root = reference_root()
    root.mkdir(parents=True, exist_ok=True)
    name = Path(urlparse(url).path).name
    if not _PART_FILE.match(name):
        name = f"{sku}_(RevWeb).pdf"
    dest = root / name
    dest.write_bytes(content)
    return dest


def fetch_and_store(part: str, *, part_key: str = "") -> dict[str, Any]:
    """English product page for one inventory part -> local PDF + limits yaml.

    Never writes into #Test_Database.
    """
    sku = _norm_part(part)
    pk = str(part_key or sku).strip().lower()
    path = PARTS_DIR / f"{pk}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"no part yaml {path.name} -- add the SKU we test first, then fetch")
    from ate.core.lookup import TEXT_DIR, build_index, extract_and_store_text, resolve_pdf, sync_limits_from_local

    local = resolve_pdf(sku)
    if local:
        return sync_limits_from_local(sku, part_key=pk, web_ok=False)
    hits = _search_hits(sku)
    page_url = ""
    html = ""
    for url in hits:
        try:
            html = _get(url)
        except Exception:
            continue
        if sku.lower() in html.lower():
            page_url = url
            break
    if not page_url:
        return {
            "part": sku,
            "part_key": pk,
            "pdf": "",
            "yaml": str(LIMITS_DIR / f"{pk}.yaml"),
            "note": "No English product page/PDF. Existing limits kept. Did not scrape into #Test_Database.",
        }
    pdfs = _pdf_urls(html, page_url)
    stored = ""
    for pdf_url in pdfs:
        try:
            blob = _download_pdf(pdf_url)
        except Exception:
            continue
        if not blob.startswith(b"%PDF"):
            continue
        dest = _store_reference_pdf(sku, pdf_url, blob)
        extract_and_store_text(pk, dest)
        extracted = TEXT_DIR / f"{pk}.txt"
        body = extracted.read_text(encoding="utf-8") if extracted.is_file() else ""
        if sku.lower() not in body.lower() and sku.lower() not in dest.name.lower():
            if sku.lower() not in html.lower():
                try:
                    dest.unlink()
                except Exception:
                    pass
                continue
        stored = str(dest)
        build_index(persist=True)
        break
    if stored:
        synced = sync_limits_from_local(sku, part_key=pk, web_ok=False)
        synced["url"] = page_url
        synced["downloaded"] = stored
        synced["note"] = "Saved PDF under local Reference. Did not scrape into #Test_Database."
        return synced
    return {
        "part": sku,
        "part_key": pk,
        "url": page_url,
        "pdf": "",
        "yaml": str(LIMITS_DIR / f"{pk}.yaml"),
        "note": "Product page found but no PDF. Existing limits kept.",
    }
