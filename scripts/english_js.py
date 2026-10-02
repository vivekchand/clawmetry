"""Extract literal translation arguments without executing JavaScript.

This is a lexer for the supported translation-call forms, not a JavaScript
parser or an inventory of all rendered text. Comments, regex literals and
template text are not calls. Template expressions are scanned as code.
Dynamic keys and fallback expressions remain explicit review candidates.
Use node --check separately to validate JavaScript syntax.
"""
from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_right
import re


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    start: int
    end: int
    value: str | None = None


@dataclass(frozen=True)
class Translation:
    key: str | None
    fallback: str | None
    line: int
    start: int
    end: int
    fallback_start: int | None
    fallback_end: int | None
    pending: str | None


_IDENT = re.compile(r"[$A-Za-z_][$\w]*")
_NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
_CONTROL = frozenset({"if", "while", "for", "with", "switch", "catch"})
_BEFORE_EXPRESSION = frozenset({"return", "throw", "case", "delete", "void", "typeof",
                                "instanceof", "in", "of", "yield", "await", "new"})
_ESCAPES = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "0": "\0"}


def _cooked(raw: str) -> str:
    """Decode supported JavaScript string escapes, never eval source code."""
    parts = []
    i = 0
    while i < len(raw):
        char = raw[i]
        i += 1
        if char != "\\":
            parts.append(char)
            continue
        if i == len(raw):
            raise ValueError("incomplete string escape")
        char = raw[i]
        i += 1
        if char in "\r\n":
            if char == "\r" and i < len(raw) and raw[i] == "\n":
                i += 1
            continue
        if char.isdigit() and (char != "0" or (i < len(raw) and raw[i].isdigit())):
            raise ValueError("legacy numeric string escape requires review")
        if char in ("x", "u"):
            if char == "u" and i < len(raw) and raw[i] == "{":
                stop = raw.find("}", i + 1)
                if stop < 0:
                    raise ValueError("incomplete Unicode escape")
                digits = raw[i + 1:stop]
                i = stop + 1
            else:
                size = 2 if char == "x" else 4
                digits = raw[i:i + size]
                if len(digits) != size:
                    raise ValueError("incomplete character escape")
                i += size
            if not digits or not re.fullmatch(r"[0-9a-fA-F]+", digits):
                raise ValueError("invalid character escape")
            parts.append(chr(int(digits, 16)))
        else:
            parts.append(_ESCAPES.get(char, char))
    # Join UTF-16 surrogate pairs emitted by two \uXXXX escapes.
    return "".join(parts).encode("utf-16", "surrogatepass").decode("utf-16")


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.i = 0

    def _quoted(self, quote: str) -> Token:
        start = self.i
        self.i += 1
        while self.i < len(self.source):
            char = self.source[self.i]
            self.i += 1
            if char == "\\":
                self.i += 1
            elif char == quote:
                raw = self.source[start:self.i]
                return Token("string", raw, start, self.i, _cooked(raw[1:-1]))
        raise ValueError("unterminated quoted string")

    def _template(self) -> list[Token]:
        start = self.i
        self.i += 1
        chunk = self.i
        parts = []
        interpolated = False
        while self.i < len(self.source):
            char = self.source[self.i]
            if char == "\\":
                self.i += 2
                continue
            if char == "`":
                self.i += 1
                if not interpolated:
                    raw = self.source[start:self.i]
                    return [Token("string", raw, start, self.i,
                                  _cooked(raw[1:-1].replace("\r\n", "\n")))]
                parts.append(Token("template", "`", chunk, self.i))
                return parts
            if self.source.startswith("${", self.i):
                interpolated = True
                parts.append(Token("template", "`", chunk, self.i))
                parts.append(Token("punct", "{", self.i, self.i + 2))
                self.i += 2
                parts.extend(self.code(until_brace=True))
                parts.append(Token("punct", "}", self.i - 1, self.i))
                chunk = self.i
                continue
            self.i += 1
        raise ValueError("unterminated template literal")

    def _regex(self) -> Token | None:
        start = self.i
        j = start + 1
        in_class = False
        while j < len(self.source) and self.source[j] not in "\r\n":
            char = self.source[j]
            if char == "\\":
                j += 2
                continue
            if char == "[":
                in_class = True
            elif char == "]":
                in_class = False
            elif char == "/" and not in_class:
                j += 1
                while j < len(self.source) and self.source[j].isalpha():
                    j += 1
                self.i = j
                return Token("regex", self.source[start:j], start, j)
            j += 1
        return None

    def code(self, until_brace: bool = False) -> list[Token]:
        out = []
        groups = []
        regex_allowed = True
        while self.i < len(self.source):
            start = self.i
            char = self.source[start]
            if char.isspace():
                self.i += 1
                continue
            if self.source.startswith("//", start):
                end = self.source.find("\n", start)
                self.i = len(self.source) if end < 0 else end
                continue
            if self.source.startswith("/*", start):
                end = self.source.find("*/", start + 2)
                if end < 0:
                    raise ValueError("unterminated block comment")
                self.i = end + 2
                continue
            if char in "\"'":
                out.append(self._quoted(char))
                regex_allowed = False
                continue
            if char == "`":
                out.extend(self._template())
                regex_allowed = False
                continue
            if char == "/" and regex_allowed:
                token = self._regex()
                if token:
                    out.append(token)
                    regex_allowed = False
                    continue
            match = _IDENT.match(self.source, start) or _NUMBER.match(self.source, start)
            if match:
                self.i = match.end()
                value = match.group()
                out.append(Token("word", value, start, self.i))
                regex_allowed = value in _BEFORE_EXPRESSION
                continue
            previous = out[-1].text if out else ""
            if char in "({[":
                # Distinguish expression objects from statement blocks so a
                # slash after their close is division or a regex respectively.
                object_literal = char == "{" and previous in ("=", "(", "[", ",", ":", "return")
                groups.append((char, previous in _CONTROL, object_literal))
                regex_allowed = True
            elif char in ")}]":
                if char == "}" and until_brace and not groups:
                    self.i += 1
                    return out
                if not groups or groups[-1][0] != {")": "(", "}": "{", "]": "["}[char]:
                    raise ValueError("unbalanced JavaScript grouping")
                opened, control, object_literal = groups.pop()
                regex_allowed = control if opened == "(" else opened == "{" and not object_literal
            else:
                regex_allowed = char != "."
            self.i += 1
            # Preserve these operators as tokens; => introduces a block, and
            # postfix ++/-- must not make a following division look like regex.
            if self.source[start:self.i + 1] in ("=>", "++", "--", "?."):
                self.i += 1
                if char in "+-":
                    regex_allowed = False
            out.append(Token("punct", self.source[start:self.i], start, self.i))
        if groups or until_brace:
            raise ValueError("unterminated JavaScript grouping")
        return out


def _arguments(tokens: list[Token], opened: int) -> tuple[list[list[Token]], int]:
    args = [[]]
    depth = 0
    for index in range(opened + 1, len(tokens)):
        token = tokens[index]
        if token.kind == "punct":
            if token.text == ")" and depth == 0:
                return args, index
            if token.text in "({[":
                depth += 1
            elif token.text in ")}]":
                depth -= 1
            elif token.text == "," and depth == 0:
                args.append([])
                continue
        args[-1].append(token)
    raise ValueError("unterminated translation call")


def translations(source: str, aliases: dict[str, int] | None = None) -> list[Translation]:
    """Find calls to t/window.t and explicitly configured forwarding helpers.

    Alias values give the zero-based fallback argument position. This avoids
    assuming that every helper named T uses the same argument order.
    """
    positions = {"t": 2, **(aliases or {})}
    tokens = Lexer(source).code()
    line_ends = [m.start() for m in re.finditer("\n", source)]
    result = []
    for i, token in enumerate(tokens[:-1]):
        if token.kind != "word" or token.text not in positions:
            continue
        opened = i + 1
        if tokens[opened].text == "?.":
            opened += 1
        if opened >= len(tokens) or tokens[opened].text != "(":
            continue
        if i and tokens[i - 1].text == "function":
            continue
        if i > 1 and tokens[i - 1].text == "*" and tokens[i - 2].text == "function":
            continue
        if i and tokens[i - 1].text in (".", "?."):
            if i < 2 or tokens[i - 2].text not in ("window", "i18n") or token.text != "t":
                continue
        args, end = _arguments(tokens, opened)
        key_token = args[0][0] if len(args[0]) == 1 and args[0][0].kind == "string" else None
        at = positions[token.text]
        fallback_tokens = args[at] if len(args) > at else []
        fb = fallback_tokens[0] if len(fallback_tokens) == 1 and fallback_tokens[0].kind == "string" else None
        reasons = []
        if not key_token:
            reasons.append("dynamic key")
        if fallback_tokens and not fb:
            reasons.append("dynamic fallback")
        result.append(Translation(
            key_token.value if key_token else None, fb.value if fb else None,
            bisect_right(line_ends, token.start) + 1, token.start, tokens[end].end,
            fb.start if fb else None, fb.end if fb else None,
            ", ".join(reasons) or None,
        ))
    return result
