"""A tiny YAML subset parser for the project's committed config files.

This intentionally supports only nested mappings and scalar values. It keeps
the first milestone dependency-free while still allowing human-readable YAML.
Switching to PyYAML later should be a contained change behind this module.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


class YamlError(ValueError):
    """Raised when the supported YAML subset cannot be parsed."""


_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?$")


def load(path: Path) -> dict[str, Any]:
    return loads(path.read_text(encoding="utf-8"))


def loads(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line:
            raise YamlError(f"line {lineno}: tabs are not supported")

        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if ":" not in stripped:
            raise YamlError(f"line {lineno}: expected a mapping entry")

        key_text, value_text = stripped.split(":", 1)
        key = _parse_key(key_text.strip(), lineno)
        value_text = value_text.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise YamlError(f"line {lineno}: invalid indentation")

        parent = stack[-1][1]
        if key in parent:
            raise YamlError(f"line {lineno}: duplicate key {key!r}")

        if value_text:
            parent[key] = _parse_scalar(value_text)
            continue

        child: dict[str, Any] = {}
        parent[key] = child
        stack.append((indent, child))

    return root


def _parse_key(text: str, lineno: int) -> str:
    value = _parse_scalar(text)
    if not isinstance(value, str) or not value:
        raise YamlError(f"line {lineno}: mapping keys must be non-empty strings")
    return value


def _parse_scalar(text: str) -> Any:
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    if text.startswith(('"', "'")):
        try:
            value = ast.literal_eval(text)
        except (SyntaxError, ValueError) as exc:
            raise YamlError(f"invalid quoted string {text!r}") from exc
        if not isinstance(value, str):
            raise YamlError(f"expected a string scalar, got {type(value).__name__}")
        return value
    if _INT_RE.match(text):
        return int(text)
    if _FLOAT_RE.match(text):
        return float(text)
    return text

