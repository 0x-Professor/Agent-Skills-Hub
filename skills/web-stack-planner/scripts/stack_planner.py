#!/usr/bin/env python3
"""
web-stack-planner script
Usage: python scripts/stack_planner.py --input <path> --output <path> --format json|md|csv [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


FRONTEND_OPTIONS = [
    "react",
    "next.js",
    "vue",
    "nuxt",
    "sveltekit",
    "angular",
    "astro",
    "plain html/css/js",
]
BACKEND_OPTIONS = [
    "node.js/express",
    "fastapi",
    "django",
    "laravel",
    "go/gin",
    "rails",
    "supabase edge functions",
    "serverless-only",
]
DATABASE_OPTIONS = [
    "postgresql",
    "mysql",
    "mongodb",
    "sqlite",
    "supabase",
    "planetscale",
    "turso",
    "redis",
    "firebase",
]
CSS_OPTIONS = [
    "tailwind css",
    "shadcn/ui",
    "chakra ui",
    "material ui",
    "ant design",
    "mantine",
    "daisyui",
    "vanilla css",
]
AUTH_OPTIONS = ["clerk", "auth.js", "supabase auth", "custom jwt"]
PAYMENT_OPTIONS = ["stripe", "paddle", "lemonsqueezy"]
EMAIL_OPTIONS = ["resend", "sendgrid"]
STORAGE_OPTIONS = ["s3", "supabase storage", "cloudflare r2"]
DEPLOY_OPTIONS = [
    "vercel",
    "netlify",
    "fly.io",
    "railway",
    "render",
    "aws",
    "gcp",
    "azure",
    "digitalocean",
    "cloudflare pages",
]
TRUE_STRINGS = {"true", "1", "yes", "y", "on"}
FALSE_STRINGS = {"false", "0", "no", "n", "off", ""}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect stack choices and produce project-config.json")
    parser.add_argument("--input", default=".", help="Path to JSON brief or directory")
    parser.add_argument("--output", default=".", help="Output file path or directory")
    parser.add_argument("--format", choices=["json", "md", "csv"], default="json")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_output_file(output_arg: str, fmt: str, stem: str) -> Path:
    out = Path(output_arg)
    if out.suffix.lower() in {".json", ".md", ".csv"}:
        return out
    return out / f"{stem}.{fmt}"


def load_input_payload(input_arg: str) -> dict[str, Any]:
    path = Path(input_arg)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    if path.is_dir():
        for candidate in ("project-brief.json", "stack-input.json", "input.json"):
            candidate_path = path / candidate
            if candidate_path.exists():
                return json.loads(candidate_path.read_text(encoding="utf-8"))
    return {}


def normalize_choice(raw: Any, allowed: list[str], fallback: str, warnings: list[str], label: str) -> str:
    value = str(raw or "").strip().lower()
    if value in allowed:
        return value
    if value:
        warnings.append(f"Unsupported {label} '{raw}', fallback to '{fallback}'")
    return fallback


def normalize_list(raw: Any, allowed: list[str]) -> list[str]:
    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, list):
        values = [str(item) for item in raw]
    else:
        values = []
    normalized = []
    for value in values:
        lower = value.strip().lower()
        if lower in allowed and lower not in normalized:
            normalized.append(lower)
    return normalized


def parse_bool(raw: Any, default: bool = False) -> tuple[bool, bool]:
    if raw is None:
        return default, True
    if isinstance(raw, bool):
        return raw, True
    if isinstance(raw, (int, float)):
        return bool(raw), True
    if isinstance(raw, str):
        value = raw.strip().lower()
        if value in TRUE_STRINGS:
            return True, True
        if value in FALSE_STRINGS:
            return False, True
    return default, False


def build_config(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    project_name = str(payload.get("project_name") or "new-web-app").strip() or "new-web-app"
    project_type = str(payload.get("project_type") or "saas").strip().lower() or "saas"
    target_audience = str(payload.get("target_audience") or "general users").strip() or "general users"
    existing_codebase = str(payload.get("existing_codebase") or "none").strip() or "none"

    frontend = normalize_choice(
        payload.get("frontend_framework"),
        FRONTEND_OPTIONS,
        "next.js",
        warnings,
        "frontend framework",
    )
    backend = normalize_choice(
        payload.get("backend_framework"),
        BACKEND_OPTIONS,
        "node.js/express",
        warnings,
        "backend framework",
    )
    database = normalize_choice(
        payload.get("database"),
        DATABASE_OPTIONS,
        "postgresql",
        warnings,
        "database",
    )
    css_system = normalize_choice(
        payload.get("css_system"),
        CSS_OPTIONS,
        "tailwind css",
        warnings,
        "css system",
    )
    deployment = normalize_choice(
        payload.get("deployment_target"),
        DEPLOY_OPTIONS,
        "vercel",
        warnings,
        "deployment target",
    )

    integrations = payload.get("integrations", {})
    if not isinstance(integrations, dict):
        integrations = {}

    auth_selection = normalize_choice(
        integrations.get("auth") or payload.get("auth_provider"),
        AUTH_OPTIONS,
        "auth.js",
        warnings,
        "auth provider",
    )
    payments = normalize_list(integrations.get("payments") or payload.get("payments"), PAYMENT_OPTIONS)
    email = normalize_choice(
        integrations.get("email") or payload.get("email_provider"),
        EMAIL_OPTIONS,
        "resend",
        warnings,
        "email provider",
    )
    storage = normalize_choice(
        integrations.get("storage") or payload.get("storage_provider"),
        STORAGE_OPTIONS,
        "s3",
        warnings,
        "storage provider",
    )
    i18n_raw = integrations.get("i18n")
    if i18n_raw is None:
        i18n_raw = payload.get("i18n", False)
    i18n_enabled, i18n_valid = parse_bool(i18n_raw, default=False)
    if not i18n_valid:
        warnings.append(f"Unsupported i18n value '{i18n_raw}', fallback to 'false'")

    config = {
        "project_name": project_name,
        "project_type": project_type,
        "target_audience": target_audience,
        "authentication_needs": str(payload.get("authentication_needs") or "standard user accounts"),
        "existing_codebase": existing_codebase,
        "stack": {
            "frontend": frontend,
            "backend": backend,
            "database": database,
            "css_system": css_system,
        },
        "integrations": {
            "auth": auth_selection,
            "payments": payments,
            "email": email,
            "storage": storage,
            "i18n": i18n_enabled,
        },
        "deployment": {"target": deployment},
    }
    return config, warnings


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
            "## Artifacts",
        ]
        lines.extend([f"- {item}" for item in result["artifacts"]])
        lines.extend(
            [
                "",
                "## Stack",
                f"- frontend: {result['details']['project_config']['stack']['frontend']}",
                f"- backend: {result['details']['project_config']['stack']['backend']}",
                f"- database: {result['details']['project_config']['stack']['database']}",
                f"- css_system: {result['details']['project_config']['stack']['css_system']}",
            ]
        )
        output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["field", "value"])
        writer.writerow(["status", result["status"]])
        writer.writerow(["summary", result["summary"]])
        for key, value in result["details"]["project_config"]["stack"].items():
            writer.writerow([f"stack.{key}", value])
        writer.writerow(["deployment.target", result["details"]["project_config"]["deployment"]["target"]])


def main() -> int:
    args = parse_args()
    payload = load_input_payload(args.input)
    config, warnings = build_config(payload)

    report_path = resolve_output_file(args.output, args.format, "stack-planner-report")
    output_root = report_path.parent
    config_path = output_root / "project-config.json"

    if not args.dry_run:
        config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    artifacts = [str(report_path)]
    if not args.dry_run:
        artifacts.insert(0, str(config_path))

    result = {
        "status": "warning" if warnings else "ok",
        "summary": "Validated stack selections and prepared canonical project config",
        "artifacts": artifacts,
        "details": {
            "project_config": config,
            "validation_warnings": warnings,
            "dry_run": args.dry_run,
        },
    }
    render_result(result, report_path, args.format)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
