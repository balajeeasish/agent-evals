# agent-evals

[![CI](https://github.com/balajeeasish/agent-evals/actions/workflows/ci.yml/badge.svg)](https://github.com/balajeeasish/agent-evals/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight, dependency-free harness for testing AI agents: golden tasks, deterministic checks, LLM judges, and regression reports.

## Why evals matter for shipping agents

Demos are easy. Shipping is hard. An agent that works in a demo can break silently when you change a prompt, swap a model, or add a tool, and "it seemed fine in testing" is not a quality bar. Evals turn that into a number you can track: a suite of golden tasks that runs the same way every time, so regressions surface before your users find them.

agent-evals is built for the tight loop: define a task once, run it on every change, and compare runs over time to see what got fixed and what regressed.

## Quickstart (under 5 minutes)

Requires Python 3.10 or newer. There are no third-party dependencies, not even for the test suite (pytest is only needed if you want to run the repo's own tests).

```bash
git clone https://github.com/balajeeasish/agent-evals.git
cd agent-evals
python3 examples/run_demo.py
```

This runs six sample tasks against a toy template-based agent (no API key needed), prints a markdown report, and saves the full results as JSON under `runs/`.

## Example output

```
# Eval Report: demo-agent

Run `20260930T171852Z` at 2026-09-30T17:18:52+00:00

**5/6 passed (83%)**, 1 failed

## Results

| Task | Result | Notes |
| --- | --- | --- |
| summarize_short | PASS | all checks passed |
| extract_json | PASS | all checks passed |
| refusal_harmful_request | PASS | all checks passed |
| strict_format_yes_no | PASS | all checks passed |
| code_fix_off_by_one | FAIL | contains('range(n + 1)'): FAILED |
| long_input_brief | PASS | all checks passed |

## Failures

### code_fix_off_by_one
- Check `contains('range(n + 1)')` failed: output does not contain 'range(n + 1)'
- Output: `def total(n): ...`
```

## Writing your own eval

An agent is any callable that takes a prompt string and returns an output string:

```python
from agent_evals import EvalTask, EvalRunner, contains, json_valid, markdown_report

def my_agent(prompt: str) -> str:
    ...  # call your agent here

tasks = [
    EvalTask(
        name="extract_contact",
        prompt="Extract the name and email as JSON: contact Jane Doe at jane.doe@example.com",
        checks=[json_valid(required_keys=["name", "email"])],
        tags=["extraction"],
    ),
    EvalTask(
        name="stays_brief",
        prompt="Summarize this in under 200 characters: ...",
        checks=[max_length(200)],
        tags=["robustness"],
    ),
]

runner = EvalRunner(agent_name="my-agent")
result = runner.run(my_agent, tasks)
print(markdown_report(result))  # full JSON also saved to runs/<timestamp>.json
```

Track progress across versions with run comparison:

```python
from agent_evals import compare_runs

print(compare_runs("runs/20260901T120000Z.json", "runs/20260930T171852Z.json"))
# ## Fixed (2) ... ## Regressed (0) ...
```

## Checks

Deterministic checks in `agent_evals.checks`, each returning a pass/fail result with a detail message:

- `contains(substring)` / `not_contains(substring)`: keyword presence or absence
- `regex_match(pattern)`: strict output formats, such as `^(YES|NO)$`
- `json_valid(required_keys=[...])`: structured output parsing
- `equals(expected)`: exact-match assertions
- `max_length(n)`: brevity and cost control

## Judges

For open-ended tasks where no regex will do, plug in a judge and wrap it as a check with `judge_check(judge, task)`:

- `KeywordJudge(required=[...], forbidden=[...])`: fast, deterministic scoring with no API calls.
- `OpenAICompatibleJudge`: calls any OpenAI-compatible chat completions endpoint using only the Python standard library. Reads `OPENAI_API_KEY` from the environment and skips gracefully (recorded as skipped, not failed) when the key is missing.

## Architecture

```
src/agent_evals/
  task.py     EvalTask dataclass: name, prompt, checks, tags
  checks.py   deterministic check factories -> CheckResult(passed, detail)
  judge.py    Judge protocol, KeywordJudge, OpenAICompatibleJudge (stdlib urllib),
              judge_check() adapter, JudgeSkipped for graceful skipping
  runner.py   EvalRunner: runs tasks against an agent function, records per-task
              results, saves JSON to runs/<timestamp>.json
  report.py   markdown_report(), compare_runs() for fixed/regressed tracking
evals/
  sample_suite.py  6 sample tasks covering summarization, JSON extraction,
                   refusal, strict format, code fix, and long-input robustness
examples/
  demo_agent.py    toy template-based agent, no API key required
  run_demo.py      runs the sample suite and prints the markdown report
tests/
  test_checks.py   13 tests for every check factory
  test_runner.py   runner counts, JSON persistence, agent-crash handling,
                   judge skipping, run comparison
```

## Roadmap

- Parallel task execution for large suites
- HTML report rendering alongside markdown
- First-class CI integration (JUnit XML output, nonzero exit on regression)
- More judges: local-model judges, pairwise preference judges
- Dataset versioning so suites evolve without breaking comparisons

## Contributing

Contributions are welcome. Keep the dependency-free philosophy: the core package must stay standard-library only.

1. Fork the repo and create a feature branch.
2. Add tests for any new behavior.
3. Run `python3 -m pytest -q` from the repo root and make sure everything passes.
4. Open a pull request describing what changed and why.

## License

MIT. See [LICENSE](LICENSE) for details.
