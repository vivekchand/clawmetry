"""Read supported argparse prose fields without importing the source module.

This extracts literal parser help, not printed output, logs, or Python text
in general. Dynamic fields remain visible as review candidates.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass


PROSE_FIELDS = frozenset({"help", "description", "epilog", "title"})
PARSER_CALLS = frozenset({"ArgumentParser", "add_parser", "add_argument", "add_subparsers"})


@dataclass(frozen=True)
class HelpText:
    key: str
    line: int
    text: str | None
    pending: str | None = None


def argparse_help(source: str) -> list[HelpText]:
    """Extract constant strings, including adjacent Python string literals.

    Do not infer the value of names, formatted strings, or computed fields.
    Source syntax errors fail extraction instead of producing an empty list.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"invalid Python at line {exc.lineno}: {exc.msg}") from exc
    messages = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = (node.func.attr if isinstance(node.func, ast.Attribute)
                else node.func.id if isinstance(node.func, ast.Name) else "")
        if name not in PARSER_CALLS:
            continue
        owner = ast.unparse(node.func)
        option = (node.args[0].value if node.args and isinstance(node.args[0], ast.Constant)
                  and isinstance(node.args[0].value, str) else "parser")
        for kw in node.keywords:
            if kw.arg not in PROSE_FIELDS:
                continue
            key = f"{owner}.{option}.{kw.arg}"
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                value = kw.value.value
                messages.append(HelpText(key, kw.value.lineno, value,
                                         None if value.strip() else "empty help field"))
            elif (isinstance(kw.value, ast.Attribute) and kw.value.attr == "SUPPRESS"
                  and isinstance(kw.value.value, ast.Name) and kw.value.value.id == "argparse"):
                # Explicitly hidden help has no text displayed to the user.
                continue
            else:
                messages.append(HelpText(key, kw.value.lineno, None, "dynamic help field"))
    return sorted(messages, key=lambda message: (message.line, message.key))
