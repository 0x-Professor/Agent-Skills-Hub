#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

STACK_SCRIPT = "skills/web-stack-planner/scripts/stack_planner.py"
PIPELINE_SCRIPTS = [
    "skills/web-ux-architect/scripts/ux_architect.py",
    "skills/web-frontend-designer/scripts/frontend_designer.py",
    "skills/web-backend-builder/scripts/backend_builder.py",
    "skills/web-auth-integrator/scripts/auth_integrator.py",
    "skills/web-database-validator/scripts/database_validator.py",
    "skills/web-api-tester/scripts/api_tester.py",
    "skills/web-frontend-tester/scripts/frontend_tester.py",
    "skills/web-security-auditor/scripts/security_auditor.py",
    "skills/web-deploy-launcher/scripts/deploy_launcher.py",
]
EXPECTED_REPORTS = [
    "ux-report.json",
    "frontend-report.json",
    "backend-report.json",
    "auth-report.json",
    "db-validation-report.json",
    "api-test-report.json",
    "frontend-test-report.json",
    "security-report.json",
    "deploy-report.json",
]


class ScenarioError(RuntimeError):
    pass


def assert_output_contract(payload: dict, label: str) -> None:
    for key in ("status", "summary", "artifacts", "details"):
        if key not in payload:
            raise ScenarioError(f"{label}: missing key '{key}'")
    if payload["status"] not in {"ok", "warning", "error"}:
        raise ScenarioError(f"{label}: invalid status '{payload['status']}'")
    if not isinstance(payload["artifacts"], list):
        raise ScenarioError(f"{label}: artifacts must be a list")
    if not isinstance(payload["details"], dict):
        raise ScenarioError(f"{label}: details must be an object")


def run_script(script_rel: str, input_path: Path, output_path: Path, dry_run: bool) -> dict:
    script_path = ROOT / script_rel
    if not script_path.exists():
        raise ScenarioError(f"missing script: {script_rel}")

    cmd = [
        sys.executable,
        str(script_path),
        "--input",
        str(input_path),
        "--output",
        str(output_path),
        "--format",
        "json",
    ]
    if dry_run:
        cmd.append("--dry-run")

    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ScenarioError(
            f"{script_rel}: command failed\ncmd={' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    if not output_path.exists():
        raise ScenarioError(f"{script_rel}: output file not created ({output_path})")
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert_output_contract(data, script_rel)
    return data


def assert_report_contract(path: Path) -> None:
    if not path.exists():
        raise ScenarioError(f"missing report: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert_output_contract(payload, str(path))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        stack_input = root / "stack-input.json"
        stack_input.write_text(
            json.dumps(
                {
                    "project_name": "Nova Commerce",
                    "project_type": "e-commerce",
                    "target_audience": "D2C shoppers",
                    "authentication_needs": "buyers and admins",
                    "existing_codebase": "none",
                    "frontend_framework": "next.js",
                    "backend_framework": "node.js/express",
                    "database": "postgresql",
                    "css_system": "tailwind css",
                    "deployment_target": "vercel",
                    "integrations": {
                        "auth": "auth.js",
                        "payments": ["stripe"],
                        "email": "resend",
                        "storage": "s3",
                        "i18n": True,
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # 1) Run stack planner dry-run.
        stack_dry_output = root / "stack-dry-run.json"
        run_script(STACK_SCRIPT, stack_input, stack_dry_output, dry_run=True)

        # 2) Run stack planner non-dry-run and require canonical config.
        stack_live_output = root / "stack-live.json"
        run_script(STACK_SCRIPT, stack_input, stack_live_output, dry_run=False)
        config_path = root / "project-config.json"
        if not config_path.exists():
            raise ScenarioError("web-stack-planner: project-config.json was not generated")
        config = json.loads(config_path.read_text(encoding="utf-8"))
        for required_key in ("project_name", "project_type", "stack", "integrations", "deployment"):
            if required_key not in config:
                raise ScenarioError(f"web-stack-planner: project-config.json missing '{required_key}'")

        # 3) Run downstream scripts in dry-run mode and confirm config wiring.
        for script_rel in PIPELINE_SCRIPTS:
            dry_output = root / f"{Path(script_rel).stem}-dry.json"
            result = run_script(script_rel, root, dry_output, dry_run=True)
            details = result.get("details", {})
            if "project_config_path" in details and not details["project_config_path"]:
                raise ScenarioError(f"{script_rel}: expected non-empty project_config_path")

        # 4) Run downstream scripts non-dry-run to emit canonical report files.
        artifact_dir = root / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        for script_rel in PIPELINE_SCRIPTS:
            live_output = artifact_dir / f"{Path(script_rel).stem}-live.json"
            run_script(script_rel, root, live_output, dry_run=False)

        # 5) Validate every *-report.json contract.
        for report_name in EXPECTED_REPORTS:
            assert_report_contract(artifact_dir / report_name)

    summary = {
        "status": "ok",
        "summary": "Web builder pipeline scenario checks passed",
        "skills_tested": 10,
        "reports_validated": len(EXPECTED_REPORTS),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScenarioError as exc:
        print(f"Web builder scenario failure: {exc}")
        raise SystemExit(1)
