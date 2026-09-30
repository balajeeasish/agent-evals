"""agent-evals: a lightweight, dependency-free eval harness for AI agents."""

from .task import EvalTask
from .checks import (
    CheckResult,
    contains,
    not_contains,
    regex_match,
    json_valid,
    equals,
    max_length,
)
from .judge import (
    Judge,
    JudgeResult,
    JudgeSkipped,
    KeywordJudge,
    OpenAICompatibleJudge,
    judge_check,
)
from .runner import EvalRunner, RunResult, TaskResult, CheckOutcome
from .report import markdown_report, compare_runs, load_run

__all__ = [
    "EvalTask",
    "CheckResult",
    "contains",
    "not_contains",
    "regex_match",
    "json_valid",
    "equals",
    "max_length",
    "Judge",
    "JudgeResult",
    "JudgeSkipped",
    "KeywordJudge",
    "OpenAICompatibleJudge",
    "judge_check",
    "EvalRunner",
    "RunResult",
    "TaskResult",
    "CheckOutcome",
    "markdown_report",
    "compare_runs",
    "load_run",
]

__version__ = "0.1.0"
