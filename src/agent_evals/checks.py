"""Deterministic output checks.

Each factory returns a callable with the signature ``output -> CheckResult``.
Factories attach a ``description`` attribute so reports can label each check.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class CheckResult:
    passed: bool
    detail: str = ""


def _named(
    fn: Callable[[str], CheckResult], description: str
) -> Callable[[str], CheckResult]:
    fn.description = description  # type: ignore[attr-defined]
    return fn


def contains(
    substring: str, case_sensitive: bool = False
) -> Callable[[str], CheckResult]:
    """Passes when the output contains the substring (case-insensitive by default)."""

    def check(output: str) -> CheckResult:
        haystack = output if case_sensitive else output.lower()
        needle = substring if case_sensitive else substring.lower()
        if needle in haystack:
            return CheckResult(True, f"found {substring!r}")
        return CheckResult(False, f"output does not contain {substring!r}")

    return _named(check, f"contains({substring!r})")


def not_contains(
    substring: str, case_sensitive: bool = False
) -> Callable[[str], CheckResult]:
    """Passes when the output does NOT contain the substring."""

    def check(output: str) -> CheckResult:
        haystack = output if case_sensitive else output.lower()
        needle = substring if case_sensitive else substring.lower()
        if needle not in haystack:
            return CheckResult(True, f"{substring!r} absent as expected")
        return CheckResult(False, f"output unexpectedly contains {substring!r}")

    return _named(check, f"not_contains({substring!r})")


def regex_match(pattern: str, flags: int = 0) -> Callable[[str], CheckResult]:
    """Passes when the regular expression matches somewhere in the output."""

    compiled = re.compile(pattern, flags)

    def check(output: str) -> CheckResult:
        if compiled.search(output):
            return CheckResult(True, f"pattern {pattern!r} matched")
        return CheckResult(False, f"pattern {pattern!r} did not match")

    return _named(check, f"regex_match({pattern!r})")


def json_valid(
    required_keys: tuple[str, ...] = (),
) -> Callable[[str], CheckResult]:
    """Passes when the output parses as JSON, optionally with required keys."""

    def check(output: str) -> CheckResult:
        try:
            data = json.loads(output)
        except json.JSONDecodeError as exc:
            return CheckResult(False, f"invalid JSON: {exc}")
        missing = [
            key for key in required_keys if not (isinstance(data, dict) and key in data)
        ]
        if missing:
            return CheckResult(False, f"JSON is missing required keys: {missing}")
        return CheckResult(True, "valid JSON")

    return _named(check, f"json_valid(required_keys={list(required_keys)})")


def equals(expected: str, strip: bool = True) -> Callable[[str], CheckResult]:
    """Passes when the output equals the expected string (stripped by default)."""

    def check(output: str) -> CheckResult:
        actual = output.strip() if strip else output
        wanted = expected.strip() if strip else expected
        if actual == wanted:
            return CheckResult(True, "output matches expected value")
        return CheckResult(False, f"expected {wanted!r}, got {actual!r}")

    return _named(check, f"equals({expected!r})")


def max_length(n: int) -> Callable[[str], CheckResult]:
    """Passes when the output is at most n characters long."""

    def check(output: str) -> CheckResult:
        if len(output) <= n:
            return CheckResult(True, f"length {len(output)} is within {n}")
        return CheckResult(False, f"length {len(output)} exceeds limit of {n}")

    return _named(check, f"max_length({n})")
