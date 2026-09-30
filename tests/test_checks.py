"""Tests for the deterministic check factories."""
from agent_evals.checks import (
    contains,
    not_contains,
    regex_match,
    json_valid,
    equals,
    max_length,
)


def test_contains_pass():
    assert contains("hello")("well, hello there").passed


def test_contains_fail_reports_detail():
    result = contains("hello")("goodbye")
    assert not result.passed
    assert "hello" in result.detail


def test_contains_case_insensitive_by_default():
    assert contains("solar")("Solar panels").passed


def test_contains_case_sensitive():
    assert not contains("solar", case_sensitive=True)("Solar panels").passed


def test_not_contains_pass():
    assert not_contains("bomb")("have a nice day").passed


def test_not_contains_fail():
    result = not_contains("bomb")("this is a bomb")
    assert not result.passed
    assert "bomb" in result.detail


def test_regex_match_pass_and_fail():
    assert regex_match(r"^(YES|NO)$")("YES").passed
    assert not regex_match(r"^(YES|NO)$")("MAYBE").passed


def test_json_valid_accepts_valid_json():
    assert json_valid()('{"a": 1}').passed


def test_json_valid_rejects_garbage():
    result = json_valid()("not json at all")
    assert not result.passed
    assert "invalid JSON" in result.detail


def test_json_valid_required_keys():
    check = json_valid(required_keys=["name"])
    assert check('{"name": "x"}').passed
    missing = check('{"other": 1}')
    assert not missing.passed
    assert "name" in missing.detail


def test_equals_strips_by_default():
    assert equals("YES")("  YES\n").passed
    assert not equals("YES")("NO").passed


def test_max_length_boundary():
    assert max_length(5)("12345").passed
    too_long = max_length(5)("123456")
    assert not too_long.passed
    assert "exceeds" in too_long.detail
