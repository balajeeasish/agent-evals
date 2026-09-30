"""Runs eval tasks against an agent function and persists results as JSON."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .checks import CheckResult
from .judge import JudgeSkipped
from .task import EvalTask


def _check_name(check: Callable) -> str:
    return getattr(check, "description", None) or getattr(check, "__name__", "check")


@dataclass
class CheckOutcome:
    name: str
    passed: bool | None  # None means skipped (for example, judge unavailable)
    detail: str = ""


@dataclass
class TaskResult:
    task_name: str
    passed: bool
    skipped: bool
    output: str
    error: str | None
    duration_s: float
    checks: list[CheckOutcome] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> TaskResult:
        return cls(
            task_name=data["task_name"],
            passed=data["passed"],
            skipped=data["skipped"],
            output=data.get("output", ""),
            error=data.get("error"),
            duration_s=data.get("duration_s", 0.0),
            checks=[CheckOutcome(**c) for c in data.get("checks", [])],
        )


@dataclass
class RunResult:
    run_id: str
    timestamp: str
    agent: str
    results: list[TaskResult] = field(default_factory=list)
    path: str | None = None

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed and not r.skipped)

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> RunResult:
        return cls(
            run_id=data["run_id"],
            timestamp=data["timestamp"],
            agent=data["agent"],
            results=[TaskResult.from_dict(r) for r in data.get("results", [])],
            path=data.get("path"),
        )


class EvalRunner:
    """Runs a suite of EvalTasks against an agent function.

    ``agent_fn`` is any callable taking a prompt string and returning an
    output string. An exception raised by the agent fails that task but
    never crashes the harness. Each run is saved as JSON under ``runs_dir``
    so runs can be compared over time.
    """

    def __init__(self, runs_dir: str | Path = "runs", agent_name: str = "agent") -> None:
        self.runs_dir = Path(runs_dir)
        self.agent_name = agent_name

    def run(
        self, agent_fn: Callable[[str], str], tasks: list[EvalTask]
    ) -> RunResult:
        results = [self._run_task(agent_fn, task) for task in tasks]
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        result = RunResult(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent=self.agent_name,
            results=results,
        )
        result.path = str(self._save(result))
        return result

    def _run_task(
        self, agent_fn: Callable[[str], str], task: EvalTask
    ) -> TaskResult:
        start = time.perf_counter()
        error: str | None = None
        try:
            raw = agent_fn(task.prompt)
            output = "" if raw is None else str(raw)
        except Exception as exc:
            output = ""
            error = f"{type(exc).__name__}: {exc}"
        duration = time.perf_counter() - start

        outcomes: list[CheckOutcome] = []
        if error is None:
            for check in task.checks:
                try:
                    check_result: CheckResult = check(output)
                    outcomes.append(
                        CheckOutcome(
                            _check_name(check), bool(check_result.passed), check_result.detail
                        )
                    )
                except JudgeSkipped as exc:
                    outcomes.append(CheckOutcome(_check_name(check), None, str(exc)))

        decided = [o for o in outcomes if o.passed is not None]
        if error is not None:
            passed, skipped = False, False
        else:
            passed = all(o.passed for o in decided)
            skipped = not decided
        return TaskResult(
            task_name=task.name,
            passed=passed,
            skipped=skipped,
            output=output,
            error=error,
            duration_s=round(duration, 4),
            checks=outcomes,
        )

    def _save(self, result: RunResult) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.runs_dir / f"{result.run_id}.json"
        path.write_text(json.dumps(result.to_dict(), indent=2))
        return path
