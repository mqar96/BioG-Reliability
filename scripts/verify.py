"""Run quality gates and bind fresh test evidence to the exact source snapshot."""

import argparse
import subprocess
import sys
from pathlib import Path

from biog_reliability.provenance import run_context
from biog_reliability.reporting import sha256, write_json

ROOT = Path(__file__).resolve().parents[1]


def main(software_only=False):
    out = ROOT / "results/validation"
    out.mkdir(parents=True, exist_ok=True)
    commands = [
        ["ruff", "check", "."],
        ["ruff", "format", "--check", "."],
        ["pip", "check"],
        [
            "pytest",
            "--cov=biog_reliability",
            "--cov-report=json:results/coverage.json",
            "--cov-report=term-missing",
            "--junitxml=results/test-results.xml",
        ],
        ["build", "--no-isolation"],
    ]
    if software_only:
        commands[3].extend(["-m", "not realdata"])
    context = run_context(ROOT)
    context["scope"] = "software-only; research tests deselected" if software_only else "full suite"
    status = []
    for command in commands:
        result = subprocess.run(
            [sys.executable, "-m", *command],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        (out / f"{command[0]}-{len(status)}.txt").write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        print(command, result.returncode, flush=True)
        status.append({"command": command, "exit_code": result.returncode})
    context["checks"] = status
    context["test_report_sha256"] = sha256(ROOT / "results/test-results.xml")
    write_json(out / "verification.json", context)
    if any(s["exit_code"] for s in status):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--software-only", action="store_true")
    main(parser.parse_args().software_only)
