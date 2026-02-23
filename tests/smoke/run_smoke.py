#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "smoke" / "fixtures"

SCRIPT_CASES = [
    ("skills/skill-creator-pro/scripts/generate_skill_starter.py", "skill_creator_input.json"),
    ("skills/skill-creator-pro/scripts/validate_skill_pack.py", "skill_creator_input.json"),
    ("skills/cyber-kev-triage/scripts/kev_triage.py", "cyber_kev_input.json"),
    ("skills/cyber-ir-playbook/scripts/ir_timeline_report.py", "cyber_ir_input.json"),
    ("skills/cyber-owasp-review/scripts/map_findings_to_owasp.py", "cyber_owasp_input.json"),
    ("skills/ml-experiment-tracker/scripts/build_experiment_plan.py", "ml_experiment_input.json"),
    ("skills/ml-model-eval-benchmark/scripts/benchmark_models.py", "ml_benchmark_input.json"),
    ("skills/dl-transformer-finetune/scripts/build_finetune_plan.py", "dl_finetune_input.json"),
    ("skills/agentic-mcp-server-builder/scripts/scaffold_mcp_server.py", "agentic_mcp_input.json"),
    ("skills/agentic-workflow-automation/scripts/generate_workflow_blueprint.py", "agentic_workflow_input.json"),
    ("skills/google-workspace-automation/scripts/plan_workspace_automation.py", "workspace_input.json"),
    ("skills/docs-pipeline-automation/scripts/compose_docs_pipeline.py", "docs_pipeline_input.json"),
]


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, capture_output=True, text=True)


def assert_result(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("status", "summary", "artifacts", "details"):
        if key not in data:
            raise AssertionError(f"Missing key '{key}' in {path}")
    if data["status"] not in {"ok", "warning", "error"}:
        raise AssertionError(f"Invalid status '{data['status']}' in {path}")
    if not isinstance(data["artifacts"], list):
        raise AssertionError("artifacts must be a list")
    if not isinstance(data["details"], dict):
        raise AssertionError("details must be an object")


def assert_nonempty(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"Missing output file: {path}")
    if path.stat().st_size == 0:
        raise AssertionError(f"Output file is empty: {path}")


def run_for_format(script_path: Path, fixture: Path, output_path: Path, fmt: str) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(script_path),
        "--input",
        str(fixture),
        "--output",
        str(output_path),
        "--format",
        fmt,
        "--dry-run",
    ]
    return run(cmd)


def main() -> int:
    failures: list[str] = []

    for rel_script, fixture_name in SCRIPT_CASES:
        script_path = ROOT / rel_script
        fixture = FIXTURES / fixture_name

        if not script_path.exists():
            failures.append(f"{rel_script}: script not found")
            continue

        help_cmd = [sys.executable, str(script_path), "--help"]
        help_result = run(help_cmd)
        if help_result.returncode != 0:
            failures.append(
                f"{rel_script}: --help failed\nstdout={help_result.stdout}\nstderr={help_result.stderr}"
            )
            continue

        with tempfile.TemporaryDirectory() as tmpdir:
            output_json = Path(tmpdir) / "out.json"
            dry_result = run_for_format(script_path, fixture, output_json, "json")
            if dry_result.returncode != 0:
                failures.append(
                    f"{rel_script}: dry-run failed\nstdout={dry_result.stdout}\nstderr={dry_result.stderr}"
                )
                continue
            try:
                assert_result(output_json)
            except Exception as exc:
                failures.append(f"{rel_script}: invalid output contract: {exc}")
                continue

            output_md = Path(tmpdir) / "out.md"
            md_result = run_for_format(script_path, fixture, output_md, "md")
            if md_result.returncode != 0:
                failures.append(
                    f"{rel_script}: md format failed\nstdout={md_result.stdout}\nstderr={md_result.stderr}"
                )
                continue
            try:
                assert_nonempty(output_md)
            except Exception as exc:
                failures.append(f"{rel_script}: invalid markdown output: {exc}")
                continue

            output_csv = Path(tmpdir) / "out.csv"
            csv_result = run_for_format(script_path, fixture, output_csv, "csv")
            if csv_result.returncode != 0:
                failures.append(
                    f"{rel_script}: csv format failed\nstdout={csv_result.stdout}\nstderr={csv_result.stderr}"
                )
                continue
            try:
                assert_nonempty(output_csv)
            except Exception as exc:
                failures.append(f"{rel_script}: invalid csv output: {exc}")

    if failures:
        print("Smoke test failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Smoke tests passed for {len(SCRIPT_CASES)} scripts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
