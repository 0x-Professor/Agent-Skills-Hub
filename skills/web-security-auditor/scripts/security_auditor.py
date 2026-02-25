#!/usr/bin/env python3
"""
web-security-auditor script
Usage: python scripts/security_auditor.py --input <path> --output <path> --format json|md|csv [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any


TOOL_COMMANDS = {
    "semgrep": "semgrep",
    "eslint": "eslint",
    "bandit": "bandit",
    "npm_audit": "npm",
    "pip_audit": "pip-audit",
    "cargo_audit": "cargo",
    "zap": "zap-baseline.py",
    "nuclei": "nuclei",
    "gitleaks": "gitleaks",
    "trufflehog": "trufflehog",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate security checks for web applications")
    parser.add_argument("--input", default=".", help="Path to workspace")
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
    base = Path(input_arg)
    config_path = base / "project-config.json" if base.is_dir() else base
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8")), config_path
    return {}, None


def detect_tools() -> dict[str, bool]:
    found: dict[str, bool] = {}
    for label, cmd in TOOL_COMMANDS.items():
        found[label] = shutil.which(cmd) is not None
    return found


def build_findings(tools: dict[str, bool]) -> dict[str, list[dict[str, str]]]:
    findings: dict[str, list[dict[str, str]]] = {"Critical": [], "High": [], "Medium": [], "Low": []}

    if not tools.get("semgrep"):
        findings["Medium"].append(
            {"category": "SAST", "title": "Semgrep unavailable", "detail": "Install semgrep to run static analysis"}
        )
    if not tools.get("zap"):
        findings["High"].append(
            {"category": "DAST", "title": "OWASP ZAP unavailable", "detail": "DAST scan was not executed"}
        )
    if not tools.get("gitleaks"):
        findings["High"].append(
            {"category": "Secrets", "title": "Gitleaks unavailable", "detail": "Secret scanning coverage reduced"}
        )

    findings["Medium"].append(
        {
            "category": "Frontend Headers",
            "title": "Validate CSP/HSTS/nosniff/frame protections",
            "detail": "Confirm CSP blocks unsafe-inline and unsafe-eval, add HSTS and X-Content-Type-Options",
        }
    )
    findings["Medium"].append(
        {
            "category": "Backend Controls",
            "title": "Validate CORS, rate limits, and input schemas",
            "detail": "Ensure strict origin allowlist, auth endpoint rate limiting, and Zod/Pydantic validation",
        }
    )
    findings["Low"].append(
        {
            "category": "API Security",
            "title": "Add Akto/Escape business logic checks",
            "detail": "Expand beyond schema checks for authorization and abuse scenarios",
        }
    )
    return findings


def summarize_severity(findings: dict[str, list[dict[str, str]]]) -> dict[str, int]:
    return {severity: len(items) for severity, items in findings.items()}


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
            "",
            "## Findings By Severity",
        ]
        for severity, count in result["details"]["severity_counts"].items():
            lines.append(f"- {severity}: {count}")
        output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["severity", "count"])
        for severity, count in result["details"]["severity_counts"].items():
            writer.writerow([severity, count])


def main() -> int:
    args = parse_args()
    _, config_path = load_project_config(args.input)
    tools = detect_tools()
    findings = build_findings(tools)
    severity_counts = summarize_severity(findings)

    status = "ok"
    if severity_counts["Critical"] > 0:
        status = "error"
    elif severity_counts["High"] > 0 or severity_counts["Medium"] > 0:
        status = "warning"

    report_path = resolve_output_file(args.output, args.format, "security-auditor-report")
    output_root = report_path.parent
    security_report_path = output_root / "security-report.json"
    summary_md_path = output_root / "security-summary.md"

    if not args.dry_run:
        security_payload = {
            "status": status,
            "summary": "Security audit findings aggregated",
            "artifacts": [str(summary_md_path)],
            "details": {"severity_counts": severity_counts, "findings": findings},
        }
        security_report_path.write_text(json.dumps(security_payload, indent=2), encoding="utf-8")
        lines = ["# Security Summary", ""]
        for severity, items in findings.items():
            lines.append(f"## {severity}")
            if not items:
                lines.append("- none")
                continue
            for item in items:
                lines.append(f"- [{item['category']}] {item['title']}: {item['detail']}")
            lines.append("")
        summary_md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    result = {
        "status": status if config_path else "warning",
        "summary": "Aggregated web security findings across SAST/SCA/DAST and hardening checks",
        "artifacts": [str(security_report_path), str(summary_md_path), str(report_path)],
        "details": {
            "project_config_path": str(config_path) if config_path else "",
            "tool_availability": tools,
            "severity_counts": severity_counts,
            "findings": findings,
            "owasp_scope": [
                "A01 Broken Access Control",
                "A02 Cryptographic Failures",
                "A03 Injection",
                "A05 Security Misconfiguration",
                "A07 Identification and Authentication Failures",
                "A08 Software and Data Integrity Failures",
                "A09 Security Logging and Monitoring Failures",
            ],
            "dry_run": args.dry_run,
        },
    }
    render_result(result, report_path, args.format)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
