#!/usr/bin/env python3
"""
web-auth-integrator script
Usage: python scripts/auth_integrator.py --input <path> --output <path> --format json|md|csv [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


PROVIDER_STEPS = {
    "clerk": [
        "Install @clerk/nextjs or @clerk/clerk-react",
        "Wrap application root with <ClerkProvider>",
        "Protect routes with Clerk middleware/withAuth",
        "Configure Clerk webhook endpoints",
    ],
    "auth.js": [
        "Install next-auth/auth.js packages",
        "Configure OAuth providers (Google/GitHub) and credentials provider",
        "Choose JWT or database sessions",
        "Protect API routes and UI routes with auth guards",
    ],
    "supabase auth": [
        "Install @supabase/supabase-js",
        "Configure OAuth providers in Supabase dashboard",
        "Implement magic link and OTP flows",
        "Add server/client session validation",
    ],
    "custom jwt": [
        "Create /auth/register endpoint",
        "Create /auth/login endpoint",
        "Create /auth/refresh endpoint",
        "Hash passwords with bcrypt/argon2",
        "Sign and verify JWT with jose/jsonwebtoken",
        "Implement refresh-token rotation and revocation",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate auth integration plan and checklist")
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
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8")), path
    config_path = path / "project-config.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8")), config_path
    return {}, None


def normalize_provider(raw: str) -> str:
    value = raw.strip().lower()
    if value in PROVIDER_STEPS:
        return value
    if value in {"nextauth", "next-auth"}:
        return "auth.js"
    if "supabase" in value and "auth" in value:
        return "supabase auth"
    if "jwt" in value:
        return "custom jwt"
    return "auth.js"


def build_checklist(provider: str) -> list[str]:
    base = PROVIDER_STEPS.get(provider, PROVIDER_STEPS["auth.js"])
    hardening = [
        "Implement role-based access control middleware",
        "Enable CSRF protection on state-changing requests",
        "Set secure cookie flags: HttpOnly, SameSite=Strict, Secure",
        "Rotate and revoke sessions/tokens on logout",
    ]
    return base + hardening


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
            f"- auth_provider: {result['details']['auth_provider']}",
            "",
            "## Checklist",
        ]
        lines.extend([f"- {item}" for item in result["details"]["integration_checklist"]])
        output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        writer.writerow(["status", result["status"]])
        writer.writerow(["auth_provider", result["details"]["auth_provider"]])
        writer.writerow(["checklist_items", len(result["details"]["integration_checklist"])])


def main() -> int:
    args = parse_args()
    config, config_path = load_project_config(args.input)
    integrations = config.get("integrations", {}) if isinstance(config.get("integrations"), dict) else {}
    provider = normalize_provider(str(integrations.get("auth", "auth.js")))
    checklist = build_checklist(provider)
    rbac_roles = ["admin", "member", "viewer"]

    report_path = resolve_output_file(args.output, args.format, "auth-integrator-report")
    output_root = report_path.parent
    auth_report_path = output_root / "auth-report.json"
    checklist_md_path = output_root / "auth-integration-checklist.md"

    if not args.dry_run:
        checklist_md_path.write_text(
            "\n".join(["# Auth Integration Checklist", ""] + [f"- {item}" for item in checklist]) + "\n",
            encoding="utf-8",
        )
        auth_report_payload = {
            "status": "ok",
            "summary": "Generated auth integration checklist",
            "artifacts": [str(checklist_md_path)],
            "details": {
                "auth_provider": provider,
                "rbac_roles": rbac_roles,
                "csrf_enabled": True,
                "secure_cookies": ["HttpOnly", "SameSite=Strict", "Secure"],
            },
        }
        auth_report_path.write_text(json.dumps(auth_report_payload, indent=2), encoding="utf-8")

    artifacts = [str(report_path)]
    if not args.dry_run:
        artifacts = [str(auth_report_path), str(checklist_md_path), str(report_path)]

    result = {
        "status": "ok" if config_path else "warning",
        "summary": "Generated provider-specific authentication integration plan",
        "artifacts": artifacts,
        "details": {
            "project_config_path": str(config_path) if config_path else "",
            "auth_provider": provider,
            "integration_checklist": checklist,
            "rbac_roles": rbac_roles,
            "csrf_protection": True,
            "secure_cookie_flags": ["HttpOnly", "SameSite=Strict", "Secure"],
            "dry_run": args.dry_run,
        },
    }
    render_result(result, report_path, args.format)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
