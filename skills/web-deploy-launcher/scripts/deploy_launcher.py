#!/usr/bin/env python3
"""
web-deploy-launcher script
Usage: python scripts/deploy_launcher.py --input <path> --output <path> --format json|md|csv [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


TARGET_FILES = {
    "vercel": ["vercel.json"],
    "netlify": ["netlify.toml"],
    "fly.io": ["fly.toml", "Dockerfile"],
    "railway": ["Dockerfile"],
    "render": ["Dockerfile"],
    "cloudflare pages": ["wrangler.toml"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare deployment artifacts and pre-launch checklist")
    parser.add_argument("--input", default=".", help="Path to workspace with project-config.json")
    parser.add_argument("--output", default=".", help="Output file path or directory")
    parser.add_argument("--format", choices=["json", "md", "csv"], default="json")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_output_file(output_arg: str, fmt: str, stem: str) -> Path:
    out = Path(output_arg)
    if out.suffix.lower() in {".json", ".md", ".csv"}:
        return out
    return out / f"{stem}.{fmt}"


def load_project_config(input_arg: str) -> tuple[dict[str, Any], Path | None]:
    path = Path(input_arg)
    config_path = path / "project-config.json" if path.is_dir() else path
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8")), config_path
    return {}, None


def build_target_config(target: str) -> dict[str, str]:
    if target == "vercel":
        return {"vercel.json": json.dumps({"version": 2, "framework": "nextjs"}, indent=2) + "\n"}
    if target == "netlify":
        return {"netlify.toml": '[build]\ncommand = "npm run build"\npublish = "dist"\n'}
    if target == "fly.io":
        return {
            "fly.toml": 'app = "web-app"\n[build]\n  dockerfile = "Dockerfile"\n',
            "Dockerfile": "FROM node:20-alpine\nWORKDIR /app\nCOPY . .\nRUN npm ci && npm run build\nCMD [\"npm\",\"start\"]\n",
        }
    if target in {"railway", "render"}:
        return {
            "Dockerfile": "FROM node:20-alpine\nWORKDIR /app\nCOPY . .\nRUN npm ci && npm run build\nCMD [\"npm\",\"run\",\"start\"]\n"
        }
    if target == "cloudflare pages":
        return {"wrangler.toml": 'name = "web-app"\ncompatibility_date = "2026-01-01"\n'}
    return {"deployment-config.txt": f"Deployment target '{target}' requires manual configuration.\n"}


def detect_build_command(root: Path) -> list[str] | None:
    if (root / "package.json").exists():
        return ["npm", "run", "build"]
    if (root / "pyproject.toml").exists():
        return [sys.executable, "-m", "build"]
    return None


def attempt_build(root: Path, dry_run: bool) -> dict[str, Any]:
    command = detect_build_command(root)
    if command is None:
        return {"attempted": False, "status": "warning", "message": "No build manifest found"}
    if dry_run:
        return {"attempted": True, "status": "ok", "message": f"Dry-run: {' '.join(command)}"}
    proc = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    return {
        "attempted": True,
        "status": "ok" if proc.returncode == 0 else "error",
        "message": "Build succeeded" if proc.returncode == 0 else "Build failed",
        "stdout_tail": "\n".join(proc.stdout.splitlines()[-10:]),
        "stderr_tail": "\n".join(proc.stderr.splitlines()[-10:]),
    }


def read_env_example(root: Path) -> list[str]:
    env_path = root / ".env.example"
    if not env_path.exists():
        return []
    keys = []
    for line in env_path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if not clean or clean.startswith("#") or "=" not in clean:
            continue
        keys.append(clean.split("=", 1)[0])
    return keys


def render_result(result: dict[str, Any], output_file: Path, fmt: str) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        output_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return
    if fmt == "md":
        lines = [
            f"# {result['summary']}",
            "",
            f"- status: {result['status']}",
            f"- target: {result['details']['deployment_target']}",
            f"- build_status: {result['details']['build_check']['status']}",
            "",
            "## Pre-deploy Checklist",
        ]
        lines.extend([f"- {item}" for item in result["details"]["pre_deploy_checklist"]])
        output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        writer.writerow(["status", result["status"]])
        writer.writerow(["deployment_target", result["details"]["deployment_target"]])
        writer.writerow(["build_status", result["details"]["build_check"]["status"]])
        writer.writerow(["bundle_size_kb_estimate", result["details"]["bundle_size_kb_estimate"]])


def main() -> int:
    args = parse_args()
    input_root = Path(args.input) if Path(args.input).is_dir() else Path(args.input).parent
    config, config_path = load_project_config(args.input)
    deployment_target = str(config.get("deployment", {}).get("target", "vercel")).lower() if isinstance(config.get("deployment"), dict) else "vercel"
    config_files = build_target_config(deployment_target)

    build_check = attempt_build(input_root, args.dry_run)
    env_keys = read_env_example(input_root)
    pre_deploy_checklist = [
        "HTTPS enforced",
        "Sentry or equivalent monitoring configured",
        "Application logging configured",
        "Database backup strategy validated",
        "Feature flags documented",
        "Rollback plan documented",
    ]
    bundle_size_kb_estimate = 280 if deployment_target in {"vercel", "netlify", "cloudflare pages"} else 410

    status = "ok"
    if build_check["status"] == "error":
        status = "error"
    elif build_check["status"] == "warning":
        status = "warning"

    report_path = resolve_output_file(args.output, args.format, "deploy-launcher-report")
    output_root = report_path.parent
    deploy_report_path = output_root / "deploy-report.json"
    deployment_md_path = output_root / "DEPLOYMENT.md"

    created_files: list[str] = []
    if not args.dry_run:
        for filename, content in config_files.items():
            target_path = output_root / filename
            target_path.write_text(content, encoding="utf-8")
            created_files.append(str(target_path))

        deployment_md_path.write_text(
            "\n".join(
                [
                    "# Deployment Summary",
                    "",
                    f"- target: {deployment_target}",
                    f"- build_status: {build_check['status']}",
                    f"- bundle_size_kb_estimate: {bundle_size_kb_estimate}",
                    "",
                    "## Pre-Deploy Checklist",
                    *[f"- {item}" for item in pre_deploy_checklist],
                    "",
                    "## Environment Keys",
                    *(["- none detected"] if not env_keys else [f"- {key}" for key in env_keys]),
                    "",
                ]
            ),
            encoding="utf-8",
        )
        created_files.append(str(deployment_md_path))

        deploy_payload = {
            "status": status,
            "summary": "Deployment readiness artifacts generated",
            "artifacts": created_files,
            "details": {
                "deployment_target": deployment_target,
                "build_check": build_check,
                "bundle_size_kb_estimate": bundle_size_kb_estimate,
            },
        }
        deploy_report_path.write_text(json.dumps(deploy_payload, indent=2), encoding="utf-8")

    artifacts = [str(report_path)]
    if not args.dry_run:
        artifacts = [str(deploy_report_path), str(deployment_md_path), str(report_path)] + created_files

    result = {
        "status": status if config_path else "warning",
        "summary": "Prepared deployment config and launch readiness checklist",
        "artifacts": artifacts,
        "details": {
            "project_config_path": str(config_path) if config_path else "",
            "deployment_target": deployment_target,
            "generated_config_files": list(config_files.keys()),
            "build_check": build_check,
            "bundle_size_kb_estimate": bundle_size_kb_estimate,
            "env_keys_in_example": env_keys,
            "pre_deploy_checklist": pre_deploy_checklist,
            "dry_run": args.dry_run,
        },
    }
    render_result(result, report_path, args.format)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
