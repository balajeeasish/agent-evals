"""Tests for the eval runner, saved runs, and run comparison."""
import json
from pathlib import Path

from agent_evals.checks import contains
from agent_evals.judge import JudgeSkipped, KeywordJudge, judge_check
from agent_evals.report import compare_runs
from agent_evals.runner import EvalRunner
from agent_evals.task import EvalTask


def _agent(output):
    return lambda prompt: output


def test_runner_counts_and_saves_json(tmp_path):
    tasks = [
        EvalTask("t1", "prompt one", checks=[contains("ok")]),
        EvalTask("t2", "prompt two", checks=[contains("missing")]),
    ]
    runner = EvalRunner(runs_dir=tmp_path / "runs", agent_name="stub")
    result = runner.run(_agent("this is ok"), tasks)

    assert result.total == 2
    assert result.passed == 1
    assert result.failed == 1
    assert result.skipped == 0
    assert result.agent == "stub"

    saved = Path(result.path)
    assert saved.exists()
    data = json.loads(saved.read_text())
    assert data["agent"] == "stub"
    assert [r["task_name"] for r in data["results"]] == ["t1", "t2"]
    assert data["results"][0]["passed"] is True
    assert data["results"][1]["passed"] is False


def test_runner_agent_error_fails_task_without_crashing(tmp_path):
    def boom(prompt):
        raise RuntimeError("kaput")

    runner = EvalRunner(runs_dir=tmp_path / "runs")
    result = runner.run(boom, [EvalTask("t1", "p", checks=[contains("x")])])

    assert result.failed == 1
    assert result.results[0].passed is False
    assert "RuntimeError" in result.results[0].error


def test_runner_judge_skip_marks_task_skipped(tmp_path):
    judge = KeywordJudge(required=["x"])
    passing = EvalTask("t1", "p", checks=[])
    passing.checks.append(judge_check(judge, passing))

    class UnavailableJudge:
        @property
        def name(self):
            return "unavailable"

        def score(self, task, output):
            raise JudgeSkipped("no API key")

    skipped = EvalTask("t2", "p", checks=[])
    skipped.checks.append(judge_check(UnavailableJudge(), skipped))

    runner = EvalRunner(runs_dir=tmp_path / "runs")
    result = runner.run(_agent("x marks the spot"), [passing, skipped])

    assert result.results[0].passed is True
    assert result.results[1].skipped is True
    assert result.results[1].checks[0].passed is None
    assert result.skipped == 1


def test_compare_runs_reports_fixed_and_regressed(tmp_path):
    tasks = [
        EvalTask("t1", "p", checks=[contains("ok")]),
        EvalTask("t2", "p", checks=[contains("zzz")]),
    ]
    first = EvalRunner(runs_dir=tmp_path / "a").run(_agent("ok output"), tasks)
    second = EvalRunner(runs_dir=tmp_path / "b").run(_agent("zzz output"), tasks)

    report = compare_runs(first.path, second.path)

    assert "Fixed" in report
    assert "Regressed" in report
    assert "`t2`" in report  # failed before, passes now
    assert "`t1`" in report  # passed before, fails now
