"""Markdown reports for eval runs, plus run-over-run comparison."""
from __future__ import annotations

import json
from pathlib import Path

from .runner import RunResult, TaskResult


def _status(result: TaskResult) -> str:
    if result.skipped:
        return "SKIP"
    return "PASS" if result.passed else "FAIL"


def markdown_report(run: RunResult) -> str:
    """Render a RunResult as a markdown report string."""
    summary = f"**{run.passed}/{run.total} passed ({run.pass_rate:.0%})**"
    extras = []
    if run.failed:
        extras.append(f"{run.failed} failed")
    if run.skipped:
        extras.append(f"{run.skipped} skipped")
    if extras:
        summary += ", " + ", ".join(extras)

    lines = [
        f"# Eval Report: {run.agent}",
        "",
        f"Run `{run.run_id}` at {run.timestamp}",
        "",
        summary,
        "",
        "## Results",
        "",
        "| Task | Result | Notes |",
        "| --- | --- | --- |",
    ]
    for result in run.results:
        notes = []
        for check in result.checks:
            if check.passed is None:
                notes.append(f"{check.name}: skipped")
            elif not check.passed:
                notes.append(f"{check.name}: FAILED")
        if result.error:
            notes.append(f"agent error: {result.error}")
        lines.append(
            f"| {result.task_name} | {_status(result)} | "
            f"{'; '.join(notes) or 'all checks passed'} |"
        )

    failures = [r for r in run.results if not r.passed and not r.skipped]
    if failures:
        lines += ["", "## Failures", ""]
        for result in failures:
            lines.append(f"### {result.task_name}")
            for check in result.checks:
                if check.passed is False:
                    lines.append(f"- Check `{check.name}` failed: {check.detail}")
            if result.error:
                lines.append(f"- Agent raised an error: {result.error}")
            snippet = result.output[:500]
            lines.append(f"- Output: `{snippet}`")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_run(path: str | Path) -> RunResult:
    """Load a previously saved run JSON file."""
    data = json.loads(Path(path).read_text())
    return RunResult.from_dict(data)


def compare_runs(baseline_path: str | Path, current_path: str | Path) -> str:
    """Compare two saved runs and report fixed, regressed, new, and removed tasks."""
    baseline = {r.task_name: r for r in load_run(baseline_path).results}
    current = {r.task_name: r for r in load_run(current_path).results}

    def outcome(result: TaskResult) -> str:
        if result.skipped:
            return "skip"
        return "pass" if result.passed else "fail"

    fixed, regressed, new, removed = [], [], [], []
    for name, current_result in current.items():
        if name not in baseline:
            new.append(name)
        elif outcome(baseline[name]) == "fail" and outcome(current_result) == "pass":
            fixed.append(name)
        elif outcome(baseline[name]) == "pass" and outcome(current_result) == "fail":
            regressed.append(name)
    for name in baseline:
        if name not in current:
            removed.append(name)

    lines = [
        "# Run Comparison",
        "",
        f"Baseline: `{baseline_path}`",
        f"Current: `{current_path}`",
        "",
    ]

    def section(title: str, items: list[str]) -> None:
        lines.append(f"## {title} ({len(items)})")
        lines.append("")
        if items:
            lines.extend(f"- `{name}`" for name in sorted(items))
        else:
            lines.append("None")
        lines.append("")

    section("Fixed", fixed)
    section("Regressed", regressed)
    section("New tasks", new)
    section("Removed tasks", removed)
    return "\n".join(lines).rstrip() + "\n"
