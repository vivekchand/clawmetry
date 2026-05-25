#!/usr/bin/env python3
"""
Translate README.md (and other Markdown docs) into docs/i18n/<lang>/README.md
using the local `claude` CLI (Claude Code) - no API key. English README.md is
the single source of truth.

Markdown-aware: preserves headings, lists, tables, code fences (contents NOT
translated), links, URLs, image/badge tags and HTML verbatim; keeps brand terms.
Idempotent via a source-hash marker, so re-running only re-translates files whose
English source changed. Retries on transient CLI rate limits with backoff.

Usage:
  python3 scripts/i18n_translate_docs.py [--readme README.md]
      [--locales-dir clawmetry/static/locales] [--out-dir docs/i18n]
      [--only zh-CN,ja,ar] [--dry-run]
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

GLOSSARY = [
    "ClawMetry", "OpenClaw", "NVIDIA NemoClaw", "NemoClaw", "DuckDB",
    "pip install clawmetry", "cron", "OTLP", "OpenTelemetry", "PyPI", "Docker", "Pro",
]


def _meta_langs(locales_dir):
    meta = json.load(open(os.path.join(locales_dir, "_meta.json"), encoding="utf-8"))
    rows = meta if isinstance(meta, list) else list(meta.values())
    return [
        (m["code"], m.get("endonym", m["code"]))
        for m in rows
        if m.get("code") != "en" and m.get("enabled", True) and not m.get("dev")
    ]


def _translate(model, lang_name, md):
    prompt = (
        "Translate this Markdown README from English into %s. Rules:\n"
        "- Output ONLY the translated Markdown, nothing else (no preamble, no code fence around the whole thing).\n"
        "- Preserve ALL Markdown structure, headings, lists, tables, links, URLs, image/badge tags and raw HTML verbatim.\n"
        "- Do NOT translate the contents of code fences/inline code, shell commands, or URLs.\n"
        "- Keep these terms exactly as-is: %s.\n"
        "- Translate only human-readable prose; do not add or drop sections.\n"
        "- Do not use em-dashes or double-hyphens.\n\n%s"
        % (lang_name, ", ".join(GLOSSARY), md)
    )
    cmd = ["claude", "-p", prompt] + (["--model", model] if model else [])
    last = ""
    for attempt in range(6):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
            if p.returncode == 0 and p.stdout.strip():
                out = p.stdout.strip()
                if out.startswith("```"):
                    out = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", out).strip()
                return out
            last = (p.stderr or p.stdout or "").strip()[:200]
        except Exception as e:
            last = str(e)[:200]
        if attempt < 5:
            time.sleep(min(120, 20 * (attempt + 1)))
    raise RuntimeError("claude CLI failed after retries: " + last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--readme", default="README.md")
    ap.add_argument("--locales-dir", default="clawmetry/static/locales")
    ap.add_argument("--out-dir", default="docs/i18n")
    ap.add_argument("--only", default=None)
    ap.add_argument("--model", default=os.environ.get("I18N_MODEL"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = open(args.readme, encoding="utf-8").read()
    src_hash = hashlib.sha256(src.encode("utf-8")).hexdigest()[:12]
    marker = "<!-- i18n-src:%s -->" % src_hash

    langs = _meta_langs(args.locales_dir)
    if args.only:
        want = set(args.only.split(","))
        langs = [(c, n) for c, n in langs if c in want]

    done = 0
    for code, name in langs:
        out_path = os.path.join(args.out_dir, code, "README.md")
        if os.path.exists(out_path) and marker in open(out_path, encoding="utf-8").read():
            print("[%s] up to date" % code)
            continue
        print("[%s] translating%s" % (code, " (dry-run)" if args.dry_run else ""))
        if args.dry_run:
            continue
        translated = _translate(args.model, name, src)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        header = (
            "%s\n> %s translation of [README](../../../README.md), auto-generated "
            "from the English source. English is canonical; open a PR against "
            "`README.md` for content changes.\n\n" % (marker, name)
        )
        open(out_path, "w", encoding="utf-8").write(header + translated + "\n")
        done += 1
        print("[%s] wrote %s" % (code, out_path))
    print("done: %d translated" % done)
    return 0


if __name__ == "__main__":
    sys.exit(main())
