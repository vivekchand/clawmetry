#!/usr/bin/env python3
"""
ClawMetry i18n autotranslate bot.

English (`en.json`) is the single source of truth. This script fills every
enabled locale's missing/changed keys via the Claude API, prunes orphaned keys,
and enforces placeholder/markdown integrity + a do-not-translate glossary. It is
idempotent: it only spends tokens on the delta (new or changed English keys).

Used by `.github/workflows/i18n-autotranslate.yml` and reusable across repos
(pass a different --locales-dir). See docs/PRD_I18N.md section 5.

Translation engine (default `claude-cli`): shells out to the local `claude` CLI
(Claude Code), so it uses your Claude Code sign-in - NO API key. In CI, set
CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`). `--engine api` is an
optional fallback that uses the Anthropic SDK + ANTHROPIC_API_KEY.

Usage (local, zero config - Claude Code must be signed in):
  python3 scripts/i18n_autotranslate.py --locales-dir clawmetry/static/locales \
      [--since <git-ref>] [--only zh-CN,es] [--dry-run] [--engine claude-cli|api]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict

DEFAULT_MODEL = "claude-sonnet-4-6"

# ---- catalog IO -------------------------------------------------------------

def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=OrderedDict)

def _dump(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

def _git_show(ref, path):
    """Return the JSON at <ref>:<path>, or None if unavailable (first commit, etc.)."""
    try:
        out = subprocess.check_output(["git", "show", f"{ref}:{path}"], stderr=subprocess.DEVNULL)
        return json.loads(out.decode("utf-8"))
    except Exception:
        return None

# ---- integrity guards -------------------------------------------------------

_PLACEHOLDER = re.compile(r"\{[a-zA-Z0-9_]+\}|%[sd]|\{\{.*?\}\}")
_MD_LINK = re.compile(r"\[[^\]]+\]\([^)]+\)")
_HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")

def _signature(s):
    """Structural fingerprint that must survive translation."""
    return (
        sorted(_PLACEHOLDER.findall(s)),
        len(_MD_LINK.findall(s)),
        sorted(_HTML_TAG.findall(s)),
    )

def _integrity_ok(src, translated):
    return _signature(src) == _signature(translated)

# ---- the model call ---------------------------------------------------------

GLOSSARY_DEFAULT = [
    "ClawMetry", "OpenClaw", "NVIDIA NemoClaw", "NemoClaw", "DuckDB",
    "pip install clawmetry", "cron", "OTLP", "OpenTelemetry", "Pro", "Cloud",
]

def _system_prompt(lang_name, glossary):
    return (
        f"You are a professional software-localization translator. Translate UI strings from "
        f"English into {lang_name}. Rules:\n"
        f"- Return ONLY a JSON object mapping each given key to its translated string. No prose, no code fences.\n"
        f"- Keep these terms EXACTLY as-is (do not translate or transliterate): {', '.join(glossary)}.\n"
        f"- Preserve every placeholder verbatim: {{name}}, %s, {{{{x}}}}, and any HTML tags or markdown links unchanged.\n"
        f"- Do NOT use em-dashes or double-hyphens in the translation; use commas or restructure.\n"
        f"- Match the concise, confident product tone. Translate meaning, not word-for-word.\n"
        f"- Numbers, currency symbols, and code identifiers stay as-is."
    )

def _build_prompt(lang_name, glossary, items):
    return (
        _system_prompt(lang_name, glossary)
        + "\n\nTranslate the values of this JSON object. Keys are identifiers, do NOT change them. "
        "Return ONLY the JSON object with the same keys and translated values:\n\n"
        + json.dumps(items, ensure_ascii=False, indent=2)
    )

def _extract_json(text):
    """Pull a JSON object out of model output, tolerating fences/preamble."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", text).strip()
    s, e = text.find("{"), text.rfind("}")
    if s != -1 and e > s:
        text = text[s:e + 1]
    return json.loads(text)

def _translate_batch_cli(model, lang_name, glossary, items):
    """Translate via the local `claude` CLI (Claude Code) - no API key needed.
    Uses the machine's Claude Code auth (or CLAUDE_CODE_OAUTH_TOKEN in CI).

    Retries on transient failures (server-side rate limiting, flaky CLI,
    unparseable output) with exponential backoff so one throttled call does not
    abort a long multi-locale run."""
    import time as _time
    cmd = ["claude", "-p", _build_prompt(lang_name, glossary, items)]
    if model:
        cmd += ["--model", model]
    last = ""
    for attempt in range(6):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if proc.returncode == 0:
                return _extract_json(proc.stdout)
            last = (proc.stderr or proc.stdout or "").strip()[:200]
        except Exception as e:  # timeout, parse error, etc.
            last = str(e)[:200]
        if attempt < 5:
            _time.sleep(min(120, 20 * (attempt + 1)))  # 20,40,60,80,100s
    raise RuntimeError(f"claude CLI failed after retries: {last}")

def _translate_batch_api(client, model, lang_name, glossary, items):
    """Fallback: Anthropic SDK (needs ANTHROPIC_API_KEY). Only used with --engine api."""
    resp = client.messages.create(
        model=model or "claude-sonnet-4-6", max_tokens=8192,
        system=_system_prompt(lang_name, glossary),
        messages=[{"role": "user", "content": _build_prompt(lang_name, glossary, items)}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return _extract_json(text)

def _chunks(d, n):
    items = list(d.items())
    for i in range(0, len(items), n):
        yield OrderedDict(items[i:i + n])

# ---- main -------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--locales-dir", required=True)
    ap.add_argument("--since", default=None, help="git ref of the previous en.json (to detect CHANGED keys)")
    ap.add_argument("--only", default=None, help="comma-separated locale codes to limit to")
    ap.add_argument("--engine", choices=["claude-cli", "api"], default="claude-cli",
                    help="claude-cli (default): shell out to the local `claude` CLI / Claude Code, "
                         "no API key. api: Anthropic SDK (needs ANTHROPIC_API_KEY).")
    ap.add_argument("--model", default=os.environ.get("I18N_MODEL"),
                    help="model alias/id; default = the claude CLI's configured model")
    ap.add_argument("--batch-size", type=int, default=60)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    d = args.locales_dir
    en = _load(os.path.join(d, "en.json"))
    meta = _load(os.path.join(d, "_meta.json"))
    glossary = GLOSSARY_DEFAULT
    gpath = os.path.join(d, "_glossary.json")
    if os.path.exists(gpath):
        glossary = _load(gpath)

    # which English keys changed since --since (added keys are caught by "missing in target")
    changed = set()
    if args.since:
        prev = _git_show(args.since, os.path.join(d, "en.json"))
        if prev:
            changed = {k for k, v in en.items() if prev.get(k) != v}

    targets = [m for m in meta
               if m.get("code") not in ("en",) and m.get("enabled", True) and not m.get("dev")]
    if args.only:
        wanted = set(args.only.split(","))
        targets = [m for m in targets if m["code"] in wanted]

    client = None
    if not args.dry_run and args.engine == "api":
        try:
            from anthropic import Anthropic
        except ImportError:
            print("ERROR: `pip install anthropic` required for --engine api (or use --engine claude-cli)", file=sys.stderr)
            return 2
        client = Anthropic()  # reads ANTHROPIC_API_KEY

    total_translated = 0
    for m in targets:
        code, name = m["code"], m.get("endonym", m["code"])
        path = os.path.join(d, f"{code}.json")
        cur = _load(path) if os.path.exists(path) else OrderedDict()
        # prune orphans, then compute what needs translating
        cur = OrderedDict((k, v) for k, v in cur.items() if k in en)
        todo = OrderedDict((k, en[k]) for k in en if k not in cur or k in changed)

        if not todo:
            print(f"[{code}] up to date ({len(cur)} keys)")
            # still rewrite in en key-order so the file stays clean
            _dump(path, OrderedDict((k, cur[k]) for k in en if k in cur))
            continue

        print(f"[{code}] {len(todo)} keys to translate" + (" (dry-run)" if args.dry_run else ""))
        if args.dry_run:
            for k in list(todo)[:8]:
                print(f"    - {k}")
            continue

        for batch in _chunks(todo, args.batch_size):
            if args.engine == "api":
                out = _translate_batch_api(client, args.model, name, glossary, batch)
            else:
                out = _translate_batch_cli(args.model, name, glossary, batch)
            for k, src in batch.items():
                tr = out.get(k)
                if not isinstance(tr, str) or not tr.strip():
                    tr = src  # fall back to English, never blank
                elif not _integrity_ok(src, tr):
                    print(f"    ! integrity mismatch on {code}/{k} -> keeping English", file=sys.stderr)
                    tr = src
                cur[k] = tr
                total_translated += 1

        # write in en key-order so diffs are minimal
        _dump(path, OrderedDict((k, cur.get(k, en[k])) for k in en))
        print(f"[{code}] wrote {len(en)} keys")

    print(f"done: {total_translated} translations across {len(targets)} locales")
    return 0

if __name__ == "__main__":
    sys.exit(main())
