"""Run the sample suite against the toy demo agent and print the markdown report.

Usage from the repo root:
    python examples/run_demo.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent_evals.runner import EvalRunner
from agent_evals.report import markdown_report
from evals.sample_suite import build_suite
from demo_agent import demo_agent


def main() -> int:
    runner = EvalRunner(agent_name="demo-agent")
    result = runner.run(demo_agent, build_suite())
    print(markdown_report(result))
    print(f"Full JSON saved to {result.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
