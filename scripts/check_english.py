#!/usr/bin/env python3
"""Check owned English text and report incomplete extraction separately.

No external language service, parser dependency, or frontend build is needed.
Run --inventory to inspect scope; a green check covers only extracted text.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from clawmetry.english import EXPLANATION_MESSAGES, INSIGHT_MESSAGES, TURN_MESSAGES, check_text  # noqa: E402
from scripts.english_js import translations  # noqa: E402

BASELINE = "docs/english_baseline.json"
CATALOG = "clawmetry/static/locales/en.json"
KINDS = "docs/english_message_types.json"


@dataclass(frozen=True)
class Message:
    source: str
    key: str
    line: int
    text: str
    kind: str = "unclassified"


class VisibleText(HTMLParser):
    """Collect prose across inline tags; omit code, CSS, JS and comments.

    This extracts literal HTML only. Jinja output and JavaScript renderers
    remain candidates in the inventory until separately assessed.
    """
    BLOCKS = frozenset({"div", "p", "li", "ul", "ol", "section", "article",
                        "header", "footer", "h1", "h2", "h3", "h4", "h5",
                        "h6", "button", "label", "summary", "option", "td", "th"})
    SKIP = frozenset({"script", "style", "pre", "code", "svg"})
    ATTRS = frozenset({"title", "aria-label", "placeholder", "alt"})

    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.messages = []
        self.parts = []
        self.line = 1
        self.skipped = []

    def flush(self):
        value = re.sub(r"\s+", " ", "".join(self.parts)).strip()
        self.parts = []
        if re.search(r"[A-Za-z]", value):
            self.messages.append(Message(self.source, "visible", self.line, value))

    def handle_starttag(self, tag, attrs):
        if self.skipped:
            if tag in self.SKIP:
                self.skipped.append(tag)
            return
        if tag in self.SKIP:
            # Inline code is an identifier in the surrounding sentence.
            if tag == "code":
                self.parts.append(" `CMVALUE` ")
            self.skipped.append(tag)
            return
        if tag in self.BLOCKS:
            self.flush()
        if tag == "br":
            self.parts.append("\n")
        for name, value in attrs:
            if name in self.ATTRS and value and re.search(r"[A-Za-z]", value):
                self.messages.append(Message(self.source, name, self.getpos()[0], value))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self.skipped:
            if tag == self.skipped[-1]:
                self.skipped.pop()
            return
        if tag in self.BLOCKS:
            self.flush()

    def handle_data(self, data):
        if not self.skipped:
            if not self.parts:
                self.line = self.getpos()[0]
            self.parts.append(data)


def _load_object(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path}: duplicate key {key!r}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def browser_messages(root, catalog, types):
    """Literal translation fallbacks only. Other rendering stays pending."""
    messages = []
    pending = []
    errors = []
    aliases = {"app.js": {"_sigT": 2, "_cmI18nFig": 1},
               "trial-pill.js": {"tr": 2}, "trail.js": {"T": 1}}
    for path in sorted((root / "clawmetry/static/js").rglob("*.js")):
        source = path.relative_to(root).as_posix()
        try:
            calls = translations(path.read_text(encoding="utf-8"), aliases.get(path.name))
        except ValueError as exc:
            raise ValueError(f"{source}: cannot extract translation calls: {exc}") from exc
        for call in calls:
            location = f"{source}:{call.line}"
            if call.key is not None and call.key not in catalog:
                errors.append(f"{location}: missing English catalog key {call.key!r}")
            if call.fallback:
                key = call.key or "dynamic-key"
                messages.append(Message(source, "fallback." + key, call.line, call.fallback,
                                        types.get(key, "unclassified")))
                if (call.key in catalog
                        and unescape(call.fallback).strip() != unescape(catalog[call.key]).strip()):
                    errors.append(f"{location}: fallback differs from English catalog for {call.key!r}")
            if call.pending or not call.fallback:
                pending.append({"path": source, "line": call.line, "key": call.key,
                                "reason": call.pending or "no literal fallback"})
    return messages, pending, errors


def collect(root=ROOT):
    types = _load_object(root / KINDS) if (root / KINDS).exists() else {}
    catalog = _load_object(root / CATALOG)
    source = (root / CATALOG).read_text(encoding="utf-8")
    messages = []
    for key, value in catalog.items():
        if not isinstance(value, str):
            raise ValueError(f"{CATALOG}: {key} is not text")
        marker = json.dumps(key, ensure_ascii=False)
        line = source[:source.index(marker)].count("\n") + 1
        messages.append(Message(CATALOG, key, line, value, types.get(key, "unclassified")))
    unknown = set(types) - set(catalog)
    invalid = {k for k, v in types.items() if v not in ("description", "instruction", "label")}
    if unknown or invalid:
        raise ValueError(f"Message types have unknown keys or invalid types: {sorted(unknown | invalid)}")
    browser, _, errors = browser_messages(root, catalog, types)
    if errors:
        raise ValueError("\n".join(errors))
    messages.extend(browser)
    for path in sorted((root / "clawmetry/templates").rglob("*.html")):
        parser = VisibleText(path.relative_to(root).as_posix())
        text = path.read_text(encoding="utf-8")
        # Keep line numbers stable when removing template comments. Dynamic
        # expressions become identifiers, never a claim about the final text.
        text = re.sub(r"\{#[\s\S]*?#\}", lambda m: "\n" * m.group().count("\n"), text)
        text = re.sub(r"\{%[\s\S]*?%\}", lambda m: "\n" * m.group().count("\n"), text)
        text = re.sub(r"\{\{[\s\S]*?\}\}", " `CMVALUE` ", text)
        parser.feed(text)
        parser.flush()
        messages.extend(parser.messages)
    for key, value in INSIGHT_MESSAGES.items():
        messages.append(Message("clawmetry/english.py", key, 1, value, "description"))
    for key, value in TURN_MESSAGES.items():
        messages.append(Message("clawmetry/english.py", "turn." + key, 1, value, "description"))
    for key, value in EXPLANATION_MESSAGES.items():
        messages.append(Message("clawmetry/english.py", "explanation." + key, 1, value, "instruction"))
    return messages


def violations(messages):
    counts = Counter()
    details = {}
    for message in messages:
        digest = hashlib.sha256(message.text.encode("utf-8")).hexdigest()
        for finding in check_text(message.text, message.kind):
            # One exception per source/message/rule, with occurrence counts.
            # Line numbers are diagnostic only, so unrelated line movement
            # cannot invalidate existing debt or conceal a changed sentence.
            identity = "|".join((message.source, message.key, digest, finding.rule))
            counts[identity] += 1
            details[identity] = (message, finding)
    return counts, details


def inventory(root, messages, counts):
    checked_files = Counter(m.source for m in messages)
    candidates = []
    scopes = [("clawmetry/static/js", "*.js", "dynamic browser text"),
              ("clawmetry", "*.py", "CLI, generated text, and package messages"),
              ("routes", "*.py", "API and error explanations"),
              ("helpers", "*.py", "shared explanations"),
              ("desktop", "*.py", "desktop setup and messages"),
              ("docs", "*.md", "documentation")]
    for directory, pattern, purpose in scopes:
        for path in sorted((root / directory).rglob(pattern)):
            candidates.append({"path": path.relative_to(root).as_posix(),
                               "status": "extraction_and_review_pending", "purpose": purpose})
    for path in sorted(root.glob("*.md")):
        candidates.append({"path": path.name, "status": "review_pending", "purpose": "root documentation"})
    for name in ("dashboard.py", "dashboard_claudecode.py", "install.sh", "install-clawmetry.sh",
                 "install.ps1", "install-clawmetry.ps1", "install.cmd"):
        if (root / name).exists():
            candidates.append({"path": name, "status": "extraction_and_review_pending",
                               "purpose": "legacy or installer messages"})
    return {
        "standard": "ASD-STE100 Issue 9",
        "claim": "Mechanical subset only. Full compliance is not established.",
        "checked_messages": len(messages), "mechanical_findings": sum(counts.values()),
        "checked_sources": [{"path": p, "messages": n, "review": "pending"}
                            for p, n in sorted(checked_files.items())],
        "remaining_sources": candidates,
        "browser_calls_pending": browser_messages(
            root, _load_object(root / CATALOG),
            _load_object(root / KINDS) if (root / KINDS).exists() else {},
        )[1],
        "external_repositories": {"clawmetry-pro": "adapter and paid feature explanations",
                                  "clawmetry-cloud": "hosted UI, errors, email, reports",
                                  "clawmetry-landing": "public technical explanations and help"},
        "limits": ["Only literal translation fallbacks are checked in JavaScript. Other browser rendering and Python source remain pending.",
                   "Template expressions and inserted values require rendered-message review.",
                   "Source evidence and non-English translations require separate treatment.",
                   "The full dictionary, meaning, and parts of speech require editorial review."],
    }


def read_baseline(path):
    data = _load_object(path)
    if data.get("version") != 1 or not isinstance(data.get("findings"), dict):
        raise ValueError("Unsupported or malformed English baseline")
    if any(not isinstance(v, int) or isinstance(v, bool) or v < 1 for v in data["findings"].values()):
        raise ValueError("Baseline counts must be positive integers")
    return Counter(data["findings"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--inventory", action="store_true")
    ap.add_argument("--bootstrap-baseline", action="store_true", help="Create the initial baseline once")
    ap.add_argument("--update-baseline", action="store_true", help="Remove resolved debt; never add new debt")
    ap.add_argument("--base-ref", help="Compare baseline with this Git revision in CI")
    args = ap.parse_args(argv)
    try:
        messages = collect(args.root)
        actual, details = violations(messages)
        if args.inventory:
            print(json.dumps(inventory(args.root, messages, actual), indent=2))
            return 0
        path = args.root / BASELINE
        if args.bootstrap_baseline and path.exists():
            raise ValueError("Baseline already exists. Bootstrap cannot replace it.")
        baseline = Counter() if args.bootstrap_baseline else read_baseline(path)
        if args.base_ref:
            probe = subprocess.run(["git", "show", f"{args.base_ref}:{BASELINE}"],
                                   cwd=args.root, text=True, capture_output=True)
            if probe.returncode == 0:
                previous = Counter(json.loads(probe.stdout)["findings"])
                if baseline - previous:
                    raise ValueError("The baseline adds debt relative to the base revision.")
            else:
                # Only the adoption PR may introduce the baseline. An invalid
                # ref must fail instead of silently disabling this guard.
                valid = subprocess.run(["git", "cat-file", "-e", f"{args.base_ref}^{{commit}}"],
                                       cwd=args.root, capture_output=True)
                if valid.returncode:
                    raise ValueError("Cannot read the baseline base revision.")
        new = actual - baseline
        if new and not args.bootstrap_baseline:
            for identity in sorted(new):
                message, finding = details[identity]
                print(f"{message.source}:{message.line}: {finding.rule}: {finding.message} [{message.key}]")
            print(f"FAIL: {sum(new.values())} new mechanical findings.")
            return 1
        if args.bootstrap_baseline or args.update_baseline:
            path.write_text(json.dumps({"version": 1, "standard": "ASD-STE100 Issue 9",
                                        "findings": dict(sorted(actual.items()))}, indent=2) + "\n", encoding="utf-8")
        elif baseline - actual:
            print("Resolved debt remains in the baseline. Run with --update-baseline.")
            return 1
        print(f"PASS: {len(messages)} extracted messages; {sum(actual.values())} existing mechanical findings.")
        print("Mechanical subset only. Run --inventory for pending sources and review limits.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"English check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
