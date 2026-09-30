"""Judges for open-ended tasks where deterministic checks are not enough.

A judge scores an agent's output for a task. Use ``judge_check`` to wrap any
judge as a regular check so it can be listed in ``EvalTask.checks``.
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Protocol

from .checks import CheckResult

if TYPE_CHECKING:
    from .task import EvalTask


class JudgeSkipped(Exception):
    """Raised when a judge cannot run (for example, a missing API key)."""


@dataclass
class JudgeResult:
    passed: bool
    score: float
    rationale: str = ""


class Judge(Protocol):
    """Structural interface for judges."""

    @property
    def name(self) -> str: ...

    def score(self, task: EvalTask, output: str) -> JudgeResult: ...


class KeywordJudge:
    """Fast, deterministic judge based on required and forbidden keywords."""

    def __init__(
        self,
        required: tuple[str, ...] = (),
        forbidden: tuple[str, ...] = (),
    ) -> None:
        self.required = tuple(required)
        self.forbidden = tuple(forbidden)

    @property
    def name(self) -> str:
        return "keyword"

    def score(self, task: EvalTask, output: str) -> JudgeResult:
        text = output.lower()
        missing = [w for w in self.required if w.lower() not in text]
        present_forbidden = [w for w in self.forbidden if w.lower() in text]
        total = len(self.required) + len(self.forbidden)
        hits = (len(self.required) - len(missing)) + (
            len(self.forbidden) - len(present_forbidden)
        )
        score = hits / total if total else 1.0
        passed = not missing and not present_forbidden
        rationale_parts = []
        if missing:
            rationale_parts.append(f"missing required keywords: {missing}")
        if present_forbidden:
            rationale_parts.append(f"forbidden keywords present: {present_forbidden}")
        rationale = "; ".join(rationale_parts) or "all keyword expectations met"
        return JudgeResult(passed=passed, score=score, rationale=rationale)


class OpenAICompatibleJudge:
    """LLM judge over any OpenAI-compatible chat completions endpoint.

    Uses only the standard library (urllib). Reads the API key from the
    ``OPENAI_API_KEY`` environment variable unless one is passed explicitly.
    When no key is available, ``score`` raises :class:`JudgeSkipped` so the
    runner records the check as skipped instead of failed.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        api_key: str | None = None,
        timeout: int = 30,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.timeout = timeout

    @property
    def name(self) -> str:
        return f"llm:{self.model}"

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def score(self, task: EvalTask, output: str) -> JudgeResult:
        if not self.available:
            raise JudgeSkipped(
                "OPENAI_API_KEY is not set; skipping LLM judge for "
                f"task {task.name!r}."
            )
        prompt = (
            "You are an impartial evaluator of AI agent outputs. "
            "Decide whether the output satisfactorily completes the task. "
            'Respond with JSON only: {"pass": true or false, '
            '"score": a number from 0 to 1, "rationale": "one sentence"}.\n\n'
            f"Task: {task.name}\n"
            f"Prompt given to the agent: {task.prompt}\n"
            f"Agent output: {output}"
        )
        body = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise JudgeSkipped(f"LLM judge request failed: {exc}") from exc
        content = payload["choices"][0]["message"]["content"]
        data = json.loads(content)
        passed = bool(data.get("pass"))
        score = float(data.get("score", 1.0 if passed else 0.0))
        rationale = str(data.get("rationale", ""))
        return JudgeResult(passed=passed, score=score, rationale=rationale)


def judge_check(judge: Judge, task: EvalTask) -> Callable[[str], CheckResult]:
    """Wrap a judge as a check callable for ``EvalTask.checks``.

    The task is bound at wrap time because the judge needs the task context
    in addition to the agent's output.
    """

    def check(output: str) -> CheckResult:
        result = judge.score(task, output)
        return CheckResult(
            passed=result.passed,
            detail=f"[{judge.name}] score={result.score:.2f}: {result.rationale}",
        )

    check.description = f"judge:{judge.name}"  # type: ignore[attr-defined]
    return check
