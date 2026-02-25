#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class ScenarioError(RuntimeError):
    pass


def assert_output_contract(result: dict, script_rel: str) -> None:
    for key in ("status", "summary", "artifacts", "details"):
        if key not in result:
            raise ScenarioError(f"{script_rel}: missing key '{key}' in JSON output")
    if result["status"] not in {"ok", "warning", "error"}:
        raise ScenarioError(f"{script_rel}: invalid status '{result['status']}'")
    if not isinstance(result["artifacts"], list):
        raise ScenarioError(f"{script_rel}: artifacts must be a list")
    if not isinstance(result["details"], dict):
        raise ScenarioError(f"{script_rel}: details must be an object")


def run_script(
    script_rel: str,
    payload: dict,
    temp_dir: Path,
    *,
    dry_run: bool = True,
    fmt: str = "json",
    extra_args: list[str] | None = None,
) -> tuple[dict | str, Path]:
    script_path = ROOT / script_rel
    if not script_path.exists():
        raise ScenarioError(f"Script not found: {script_rel}")

    input_path = temp_dir / f"{script_path.stem}-input.json"
    output_ext = "json" if fmt == "json" else fmt
    output_path = temp_dir / f"{script_path.stem}-output.{output_ext}"
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    cmd = [
        sys.executable,
        str(script_path),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--format",
        fmt,
    ]
    if dry_run:
        cmd.append("--dry-run")
    if extra_args:
        cmd.extend(extra_args)

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise ScenarioError(
            f"{script_rel}: command failed\n"
            f"cmd={' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise ScenarioError(f"{script_rel}: missing or empty output file {output_path}")

    if fmt == "json":
        output = json.loads(output_path.read_text(encoding="utf-8"))
        assert_output_contract(output, script_rel)
        return output, output_path

    return output_path.read_text(encoding="utf-8"), output_path


def run_security_ops_scenario(temp_dir: Path) -> dict:
    kev_payload = {
        "assets": [
            {"name": "public-api", "criticality": "critical"},
            {"name": "internal-admin", "criticality": "high"},
            {"name": "reporting", "criticality": "medium"},
        ],
        "vulnerabilities": [
            {"cve": "CVE-2026-1001", "asset": "public-api", "known_exploited": True, "cvss": 9.8},
            {"cve": "CVE-2026-1002", "asset": "internal-admin", "known_exploited": True, "cvss": 8.2},
            {"cve": "CVE-2026-1003", "asset": "reporting", "known_exploited": False, "cvss": 6.7},
        ],
    }
    kev_result, _ = run_script(
        "skills/cyber-kev-triage/scripts/kev_triage.py",
        kev_payload,
        temp_dir,
    )
    assert isinstance(kev_result, dict)
    ranked = kev_result["details"]["prioritized_vulnerabilities"]
    if len(ranked) != 3:
        raise ScenarioError("cyber-kev-triage: expected 3 ranked vulnerabilities")
    scores = [row["score"] for row in ranked]
    if scores != sorted(scores, reverse=True):
        raise ScenarioError("cyber-kev-triage: vulnerabilities are not sorted by score")
    if ranked[0]["priority"] != "P1":
        raise ScenarioError("cyber-kev-triage: highest-risk vulnerability should be P1")

    owasp_payload = {
        "findings": [
            {"id": "F-1", "title": "SQL injection in public-api endpoint", "severity": "critical"},
            {"id": "F-2", "title": "Missing MFA on internal-admin", "severity": "high"},
            {"id": "F-3", "title": "Outdated dependency with CVE notice", "severity": "medium"},
        ]
    }
    owasp_result, _ = run_script(
        "skills/cyber-owasp-review/scripts/map_findings_to_owasp.py",
        owasp_payload,
        temp_dir,
    )
    assert isinstance(owasp_result, dict)
    category_counts = owasp_result["details"]["category_counts"]
    if "A03 Injection" not in category_counts:
        raise ScenarioError("cyber-owasp-review: expected A03 Injection classification")

    ir_payload = {
        "incident_id": "INC-2601",
        "events": [
            {"time": "2026-02-24T04:30:00Z", "event": "recover_service_validation", "severity": "medium"},
            {"time": "2026-02-24T03:00:00Z", "event": "contain_endpoint_traffic", "severity": "high"},
            {"time": "2026-02-24T02:15:00Z", "event": "alert_received", "severity": "high"},
        ],
    }
    ir_result, _ = run_script(
        "skills/cyber-ir-playbook/scripts/ir_timeline_report.py",
        ir_payload,
        temp_dir,
    )
    assert isinstance(ir_result, dict)
    timeline = ir_result["details"]["timeline"]
    parsed = [datetime.fromisoformat(entry["time"].replace("Z", "+00:00")) for entry in timeline]
    if parsed != sorted(parsed):
        raise ScenarioError("cyber-ir-playbook: timeline is not sorted chronologically")
    phase_total = sum(ir_result["details"]["phase_counts"].values())
    if phase_total != len(timeline):
        raise ScenarioError("cyber-ir-playbook: phase counts do not match timeline length")

    return {
        "ranked_vulnerabilities": len(ranked),
        "owasp_categories": len(category_counts),
        "ir_events": len(timeline),
    }


def run_mlops_scenario(temp_dir: Path) -> dict:
    experiment_payload = {
        "experiment_name": "fraud-detection-baseline",
        "dataset": "data/fraud.csv",
        "metrics": ["accuracy", "f1", "roc_auc"],
        "parameters": {"model": "xgboost", "max_depth": 8, "subsample": 0.9},
        "owner": "ml-platform",
    }
    exp_result, _ = run_script(
        "skills/ml-experiment-tracker/scripts/build_experiment_plan.py",
        experiment_payload,
        temp_dir,
    )
    assert isinstance(exp_result, dict)
    if "roc_auc" not in exp_result["details"]["metrics"]:
        raise ScenarioError("ml-experiment-tracker: expected roc_auc metric in output")

    finetune_payload = {
        "model_name": "distilbert-base-uncased",
        "task": "sequence-classification",
        "dataset": "imdb",
        "num_epochs": 4,
        "learning_rate": 2e-5,
        "batch_size": 16,
    }
    finetune_result, _ = run_script(
        "skills/dl-transformer-finetune/scripts/build_finetune_plan.py",
        finetune_payload,
        temp_dir,
    )
    assert isinstance(finetune_result, dict)
    if finetune_result["details"]["training_config"]["num_epochs"] != 4:
        raise ScenarioError("dl-transformer-finetune: num_epochs not applied")

    benchmark_payload = {
        "weights": {"accuracy": 0.5, "f1": 0.3, "roc_auc": 0.2},
        "models": [
            {"name": "model-a", "metrics": {"accuracy": 0.90, "f1": 0.84, "roc_auc": 0.88}},
            {"name": "model-b", "metrics": {"accuracy": 0.89, "f1": 0.88, "roc_auc": 0.91}},
            {"name": "model-c", "metrics": {"accuracy": 0.86, "f1": 0.80, "roc_auc": 0.85}},
        ],
    }
    benchmark_result, _ = run_script(
        "skills/ml-model-eval-benchmark/scripts/benchmark_models.py",
        benchmark_payload,
        temp_dir,
    )
    assert isinstance(benchmark_result, dict)
    leaderboard = benchmark_result["details"]["leaderboard"]
    if len(leaderboard) != 3:
        raise ScenarioError("ml-model-eval-benchmark: expected 3 leaderboard entries")
    if leaderboard[0]["score"] < leaderboard[1]["score"]:
        raise ScenarioError("ml-model-eval-benchmark: leaderboard ordering is invalid")

    return {
        "experiment_metrics": len(exp_result["details"]["metrics"]),
        "finetune_task": finetune_result["details"]["task"],
        "leaderboard_models": len(leaderboard),
    }


def run_agentic_automation_scenario(temp_dir: Path) -> dict:
    scaffold_root = temp_dir / "generated-mcp-server"
    mcp_payload = {
        "server_name": "ops-helper",
        "scaffold_root": str(scaffold_root),
        "tools": [
            {"name": "list_incidents", "description": "List active incidents"},
            {"name": "get_incident", "description": "Fetch incident details by id"},
        ],
    }
    mcp_result, _ = run_script(
        "skills/agentic-mcp-server-builder/scripts/scaffold_mcp_server.py",
        mcp_payload,
        temp_dir,
        dry_run=False,
        extra_args=["--allow-outside-workspace"],
    )
    assert isinstance(mcp_result, dict)
    for relative_file in mcp_result["details"]["file_map"]:
        generated = scaffold_root / relative_file
        if not generated.exists():
            raise ScenarioError(f"agentic-mcp-server-builder: missing generated file {generated}")

    workflow_payload = {
        "workflow_name": "daily-ops-sync",
        "trigger": "cron(0 9 * * 1-5)",
        "steps": [
            {"name": "collect_metrics", "type": "http", "on_failure": "retry"},
            {"name": "summarize_metrics", "type": "llm", "on_failure": "stop"},
            {"name": "publish_status", "type": "http", "on_failure": "skip"},
        ],
    }
    workflow_result, _ = run_script(
        "skills/agentic-workflow-automation/scripts/generate_workflow_blueprint.py",
        workflow_payload,
        temp_dir,
    )
    assert isinstance(workflow_result, dict)
    steps = workflow_result["details"]["steps"]
    if len(steps) != 3:
        raise ScenarioError("agentic-workflow-automation: expected 3 workflow steps")
    if any("on_failure" not in step for step in steps):
        raise ScenarioError("agentic-workflow-automation: missing on_failure in workflow steps")

    workspace_payload = {
        "automation_name": "inbox-triage-daily",
        "services": ["gmail", "sheets", "calendar"],
        "actions": [
            {"name": "fetch_unread", "service": "gmail"},
            {"name": "append_ticket_rows", "service": "sheets"},
            {"name": "create_review_event", "service": "calendar"},
        ],
    }
    workspace_result, _ = run_script(
        "skills/google-workspace-automation/scripts/plan_workspace_automation.py",
        workspace_payload,
        temp_dir,
    )
    assert isinstance(workspace_result, dict)
    scopes = workspace_result["details"]["oauth_scopes"]
    if "https://www.googleapis.com/auth/gmail.modify" not in scopes:
        raise ScenarioError("google-workspace-automation: missing expected Gmail OAuth scope")

    docs_payload = {
        "pipeline_name": "daily-ops-report",
        "sources": ["sheets://ops-metrics", "drive://incident-notes"],
        "template_doc": "docs://ops-template",
        "destination_doc": "docs://ops-report-output",
    }
    docs_result, _ = run_script(
        "skills/docs-pipeline-automation/scripts/compose_docs_pipeline.py",
        docs_payload,
        temp_dir,
    )
    assert isinstance(docs_result, dict)
    if len(docs_result["details"]["steps"]) != 4:
        raise ScenarioError("docs-pipeline-automation: expected 4 pipeline steps")

    return {
        "mcp_tools": len(mcp_result["details"]["tools"]),
        "workflow_steps": len(steps),
        "workspace_scopes": len(scopes),
        "docs_steps": len(docs_result["details"]["steps"]),
    }


def run_skill_lifecycle_scenario(temp_dir: Path) -> dict:
    generated_root = temp_dir / "generated-skills"
    starter_payload = {
        "skill_name": "scenario-test-skill",
        "category": "agentic",
        "description": "Build scenario test skill with deterministic workflows and validation guidance.",
    }
    starter_result, _ = run_script(
        "skills/skill-creator-pro/scripts/generate_skill_starter.py",
        starter_payload,
        temp_dir,
        dry_run=False,
        extra_args=["--target-dir", str(generated_root), "--allow-outside-workspace"],
    )
    assert isinstance(starter_result, dict)
    generated_skill_dir = generated_root / starter_result["details"]["skill_name"]
    required_paths = [
        generated_skill_dir / "SKILL.md",
        generated_skill_dir / "agents" / "openai.yaml",
        generated_skill_dir / "scripts",
        generated_skill_dir / "references",
        generated_skill_dir / "assets",
    ]
    for required_path in required_paths:
        if not required_path.exists():
            raise ScenarioError(f"skill-creator-pro: expected generated path {required_path}")

    validate_payload = {"skill_root": str(ROOT / "skills")}
    validate_result, _ = run_script(
        "skills/skill-creator-pro/scripts/validate_skill_pack.py",
        validate_payload,
        temp_dir,
    )
    assert isinstance(validate_result, dict)
    if validate_result["status"] != "ok":
        raise ScenarioError(
            f"skill-creator-pro: validate_skill_pack returned {validate_result['status']}"
        )
    if validate_result["details"]["errors"]:
        raise ScenarioError(
            "skill-creator-pro: validate_skill_pack returned non-empty error list"
        )

    quick_validate_proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "quick_validate.py"),
            str(generated_skill_dir),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    if quick_validate_proc.returncode != 0:
        raise ScenarioError(
            "tools/quick_validate.py failed for generated skill\n"
            f"stdout={quick_validate_proc.stdout}\nstderr={quick_validate_proc.stderr}"
        )

    validated_repo_skills = len(
        [path for path in (ROOT / "skills").iterdir() if path.is_dir() and (path / "SKILL.md").exists()]
    )
    return {"generated_skill": generated_skill_dir.name, "validated_repo_skills": validated_repo_skills}


def main() -> int:
    scenarios = []
    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        scenarios.append(("security_ops", run_security_ops_scenario(temp_dir)))
        scenarios.append(("mlops_lifecycle", run_mlops_scenario(temp_dir)))
        scenarios.append(("agentic_automation", run_agentic_automation_scenario(temp_dir)))
        scenarios.append(("skill_lifecycle", run_skill_lifecycle_scenario(temp_dir)))

    summary = {"status": "ok", "scenarios": {name: details for name, details in scenarios}}
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScenarioError as exc:
        print(f"Scenario test failure: {exc}")
        raise SystemExit(1)
