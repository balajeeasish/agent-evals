"""Eval task definition."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .checks import CheckResult


@dataclass
class EvalTask:
    """One eval: a prompt for the agent plus checks run against its output.

    checks: a list of callables, each taking the agent's output string and
    returning a CheckResult. See agent_evals.checks for factories, and
    agent_evals.judge.judge_check to wrap an LLM judge as a check.
    """

    name: str
    prompt: str
    checks: list[Callable[[str], CheckResult]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
