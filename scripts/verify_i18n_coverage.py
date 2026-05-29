#!/usr/bin/env python3
"""
i18n coverage verifier.

Reports translation coverage per locale: total keys, app.* keys, and a
"genuinely translated" percentage (values that differ from en.json). Catches
the autotranslate bot's worst failure mode -- copying English values as
translations (keys satisfied, parity tests happy, user sees English).

Three sources, in order of preference:

  1) Local files (default): clawmetry/static/locales/<code>.json
  2) Published PyPI wheel:  --pypi [VERSION] (latest if omitted)
  3) Live cloud catalog:    --cloud [BASE_URL] (default app.clawmetry.com)

Exit 0 on pass, 1 if any locale falls below the coverage floor.

Examples:

    # local files (default)
    python3 scripts/verify_i18n_coverage.py

    # check the published wheel
    python3 scripts/verify_i18n_coverage.py --pypi

    # check live cloud against pinned wheel
    python3 scripts/verify_i18n_coverage.py --cloud

    # custom floor for translation pct (default 80)
    python3 scripts/verify_i18n_coverage.py --min-translated 90

See clawmetry#2259 for the manual checklist this script automates.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_LOCALES_DIR = REPO / "clawmetry" / "static" / "locales"
DEFAULT_CLOUD_BASE = "https://app.clawmetry.com"
PYPI_INDEX = "https://pypi.org/pypi/clawmetry/json"


def _fetch(url: str, timeout: int = 20) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def _load_local(locales_dir: Path) -> tuple[list[str], dict[str, dict]]:
    meta = json.loads((locales_dir / "_meta.json").read_text(encoding="utf-8"))
    codes = [e["code"] for e in meta if e.get("enabled") and not e.get("dev")]
    catalog: dict[str, dict] = {}
    for code in codes:
        path = locales_dir / f"{code}.json"
        if path.exists():
            catalog[code] = json.loads(path.read_text(encoding="utf-8"))
    return codes, catalog


def _load_from_wheel(version: str | None) -> tuple[list[str], dict[str, dict], str]:
    if version is None:
        info = json.loads(_fetch(PYPI_INDEX))
        version = info["info"]["version"]
    meta_url = f"https://pypi.org/pypi/clawmetry/{version}/json"
    urls = json.loads(_fetch(meta_url))["urls"]
    wheel_url = next(u["url"] for u in urls if u["filename"].endswith(".whl"))
    wheel_bytes = _fetch(wheel_url)
    catalog: dict[str, dict] = {}
    codes: list[str] = []
    with zipfile.ZipFile(io.BytesIO(wheel_bytes)) as z:
        meta_name = next(
            (n for n in z.namelist() if n.endswith("static/locales/_meta.json")),
            None,
        )
        if not meta_name:
            raise RuntimeError(f"wheel {version} has no _meta.json")
        meta = json.loads(z.read(meta_name))
        codes = [e["code"] for e in meta if e.get("enabled") and not e.get("dev")]
        prefix = meta_name[: -len("_meta.json")]
        for code in codes:
            try:
                catalog[code] = json.loads(z.read(f"{prefix}{code}.json"))
            except KeyError:
                pass
    return codes, catalog, version


def _load_from_cloud(base: str) -> tuple[list[str], dict[str, dict]]:
    meta_url = f"{base.rstrip('/')}/static/locales/_meta.json"
    meta = json.loads(_fetch(meta_url))
    codes = [e["code"] for e in meta if e.get("enabled") and not e.get("dev")]
    catalog: dict[str, dict] = {}
    for code in codes:
        url = f"{base.rstrip('/')}/static/locales/{code}.json"
        try:
            catalog[code] = json.loads(_fetch(url))
        except Exception as exc:  # noqa: BLE001
            print(f"  WARN {code}: fetch failed ({exc})", file=sys.stderr)
    return codes, catalog


def _coverage_row(code: str, en: dict, loc: dict) -> dict:
    total = len(loc)
    app_keys = sum(1 for k in loc if k.startswith("app."))
    shared = [k for k in en if k in loc]
    differ = sum(1 for k in shared if loc[k] != en[k])
    translated_pct = (100 * differ // max(1, len(shared))) if code != "en" else 100
    return {
        "code": code,
        "total": total,
        "app": app_keys,
        "shared": len(shared),
        "differ": differ,
        "translated_pct": translated_pct,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--locales-dir",
        type=Path,
        default=DEFAULT_LOCALES_DIR,
        help="local locales directory (default: clawmetry/static/locales)",
    )
    src.add_argument(
        "--pypi",
        nargs="?",
        const="",
        metavar="VERSION",
        help="verify the published PyPI wheel (omit version for latest)",
    )
    src.add_argument(
        "--cloud",
        nargs="?",
        const=DEFAULT_CLOUD_BASE,
        metavar="BASE_URL",
        help=f"verify a live cloud catalog (default: {DEFAULT_CLOUD_BASE})",
    )
    parser.add_argument(
        "--min-total",
        type=int,
        default=635,
        help="minimum total keys per locale (default: 635 ~= 99%% of en source)",
    )
    parser.add_argument(
        "--min-app",
        type=int,
        default=200,
        help="minimum app.* keys per locale (default: 200, en source = 203)",
    )
    parser.add_argument(
        "--min-translated",
        type=int,
        default=80,
        help="min %% of values that differ from en (default: 80, catches English-padding)",
    )
    parser.add_argument(
        "--allow-long-tail",
        type=int,
        default=0,
        help="number of locales allowed to miss the floor (default: 0)",
    )
    args = parser.parse_args()

    src_label: str
    if args.pypi is not None:
        version = args.pypi or None
        codes, catalog, resolved = _load_from_wheel(version)
        src_label = f"pypi wheel {resolved}"
    elif args.cloud is not None:
        codes, catalog = _load_from_cloud(args.cloud)
        src_label = f"cloud {args.cloud}"
    else:
        codes, catalog = _load_local(args.locales_dir)
        src_label = f"local {args.locales_dir}"

    en = catalog.get("en")
    if not en:
        print(f"ERROR: en.json not found in {src_label}", file=sys.stderr)
        return 2

    print(f"source: {src_label}")
    print(f"en.json: total={len(en)} app.*={sum(1 for k in en if k.startswith('app.'))}")
    print()
    print(f"  {'code':<8} {'total':>6} {'app.*':>6} {'shared':>7} {'diff':>6} {'translated':>11}")
    print(f"  {'-' * 8} {'-' * 6} {'-' * 6} {'-' * 7} {'-' * 6} {'-' * 11}")

    failures: list[str] = []
    for code in codes:
        loc = catalog.get(code)
        if loc is None:
            failures.append(f"{code}: missing locale file")
            print(f"  {code:<8} {'-':>6} {'-':>6} {'-':>7} {'-':>6} {'MISSING':>11}")
            continue
        row = _coverage_row(code, en, loc)
        flag = ""
        if row["total"] < args.min_total:
            flag = " (total<floor)"
            failures.append(f"{code}: total {row['total']} < {args.min_total}")
        elif row["app"] < args.min_app:
            flag = " (app.*<floor)"
            failures.append(f"{code}: app.* {row['app']} < {args.min_app}")
        elif code != "en" and row["translated_pct"] < args.min_translated:
            flag = " (English-padded)"
            failures.append(
                f"{code}: only {row['translated_pct']}% of values differ from en (floor {args.min_translated}%)"
            )
        print(
            f"  {row['code']:<8} {row['total']:>6} {row['app']:>6} "
            f"{row['shared']:>7} {row['differ']:>6} {row['translated_pct']:>10}%{flag}"
        )

    print()
    if not failures:
        print(f"PASS: all {len(codes)} locales meet floor "
              f"(total>={args.min_total}, app.*>={args.min_app}, translated>={args.min_translated}%)")
        return 0
    if len(failures) <= args.allow_long_tail:
        print(f"PASS (long tail): {len(failures)} locale(s) under floor, allowed up to {args.allow_long_tail}")
        for f in failures:
            print(f"  - {f}")
        return 0
    print(f"FAIL: {len(failures)} locale(s) under floor")
    for f in failures:
        print(f"  - {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
