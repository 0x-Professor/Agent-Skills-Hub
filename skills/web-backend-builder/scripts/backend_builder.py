#!/usr/bin/env python3
"""
web-backend-builder script
Usage: python scripts/backend_builder.py --input <path> --output <path> --format json|md|csv [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ORM_BY_BACKEND = {
    "node.js/express": "prisma",
    "fastapi": "sqlalchemy",
    "django": "django orm",
    "laravel": "eloquent",
    "go/gin": "gorm",
    "rails": "activerecord",
    "supabase edge functions": "@supabase/supabase-js",
    "serverless-only": "platform-native data sdk",
}
ORM_BY_DATABASE = {
    "mongodb": "mongoose",
    "postgresql": "prisma",
    "mysql": "drizzle orm",
    "sqlite": "drizzle orm",
}
DEFAULT_ENTITIES = {
    "saas": ["user", "organization", "subscription", "invoice", "feature_flag"],
    "portfolio": ["user", "project", "blog_post", "contact_message"],
    "e-commerce": ["user", "product", "category", "cart", "order", "payment"],
    "api-only": ["api_key", "consumer", "usage_event"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate backend scaffold plan and endpoint inventory")
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


def infer_entities(config: dict[str, Any], input_arg: str) -> list[str]:
    direct_entities = config.get("entities")
    if isinstance(direct_entities, list) and direct_entities:
        return [str(item).strip().lower() for item in direct_entities if str(item).strip()]
    entities_file = Path(input_arg) / "entities.json"
    if entities_file.exists():
        payload = json.loads(entities_file.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            values = [str(item).strip().lower() for item in payload if str(item).strip()]
            if values:
                return values
    ptype = str(config.get("project_type", "saas")).lower()
    return DEFAULT_ENTITIES.get(ptype, DEFAULT_ENTITIES["saas"])


def build_endpoints(entities: list[str]) -> list[dict[str, str]]:
    endpoints: list[dict[str, str]] = [
        {"method": "GET", "path": "/health", "operation": "healthCheck"},
        {"method": "POST", "path": "/auth/login", "operation": "login"},
        {"method": "POST", "path": "/auth/register", "operation": "register"},
    ]
    for entity in entities:
        plural = f"{entity}s"
        endpoints.extend(
            [
                {"method": "GET", "path": f"/api/{plural}", "operation": f"list{entity.title()}"},
                {"method": "POST", "path": f"/api/{plural}", "operation": f"create{entity.title()}"},
                {"method": "GET", "path": f"/api/{plural}/{{id}}", "operation": f"get{entity.title()}"},
                {"method": "PATCH", "path": f"/api/{plural}/{{id}}", "operation": f"update{entity.title()}"},
                {"method": "DELETE", "path": f"/api/{plural}/{{id}}", "operation": f"delete{entity.title()}"},
            ]
        )
    return endpoints


def build_openapi_yaml(endpoints: list[dict[str, str]], project_name: str) -> str:
    lines = [
        "openapi: 3.0.3",
        "info:",
        f"  title: {project_name} API",
        "  version: 1.0.0",
        "paths:",
    ]
    by_path: dict[str, list[dict[str, str]]] = {}
    for endpoint in endpoints:
        by_path.setdefault(endpoint["path"], []).append(endpoint)

    for path_key in sorted(by_path):
        lines.append(f"  {path_key}:")
        for endpoint in by_path[path_key]:
            method = endpoint["method"].lower()
            lines.extend(
                [
                    f"    {method}:",
                    f"      operationId: {endpoint['operation']}",
                    "      responses:",
                    "        '200':",
                    "          description: Success",
                ]
            )
    return "\n".join(lines) + "\n"


def write_scaffold(backend_root: Path, backend: str, orm: str, entities: list[str]) -> list[str]:
    created: list[str] = []
    (backend_root / "src").mkdir(parents=True, exist_ok=True)
    (backend_root / "src" / "models").mkdir(parents=True, exist_ok=True)
    (backend_root / "src" / "routes").mkdir(parents=True, exist_ok=True)

    readme = backend_root / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Backend Scaffold",
                "",
                f"- backend: {backend}",
                f"- orm: {orm}",
                f"- entities: {', '.join(entities)}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    created.append(str(readme))

    env_example = backend_root / ".env.example"
    env_example.write_text(
        "\n".join(
            [
                "DATABASE_URL=",
                "JWT_SECRET=",
                "API_BASE_URL=",
                "FILE_UPLOAD_BUCKET=",
                "",
            ]
        ),
        encoding="utf-8",
    )
    created.append(str(env_example))
    return created


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
            f"- backend: {result['details']['backend']}",
            f"- orm: {result['details']['orm']}",
            f"- endpoints: {result['details']['endpoint_count']}",
        ]
        output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        writer.writerow(["status", result["status"]])
        writer.writerow(["backend", result["details"]["backend"]])
        writer.writerow(["database", result["details"]["database"]])
        writer.writerow(["orm", result["details"]["orm"]])
        writer.writerow(["endpoint_count", result["details"]["endpoint_count"]])


def main() -> int:
    args = parse_args()
    config, config_path = load_project_config(args.input)
    stack = config.get("stack", {}) if isinstance(config.get("stack"), dict) else {}
    backend = str(stack.get("backend", "node.js/express")).lower()
    database = str(stack.get("database", "postgresql")).lower()
    project_name = str(config.get("project_name", "Web App")).strip() or "Web App"
    entities = infer_entities(config, args.input)

    orm = ORM_BY_DATABASE.get(database, ORM_BY_BACKEND.get(backend, "prisma"))
    endpoints = build_endpoints(entities)
    openapi_text = build_openapi_yaml(endpoints, project_name)

    report_path = resolve_output_file(args.output, args.format, "backend-builder-report")
    output_root = report_path.parent
    backend_root = output_root / "backend"
    openapi_path = output_root / "openapi.yaml"
    backend_report_path = output_root / "backend-report.json"

    created: list[str] = []
    if not args.dry_run:
        created.extend(write_scaffold(backend_root, backend, orm, entities))
        openapi_path.write_text(openapi_text, encoding="utf-8")
        created.append(str(openapi_path))
        backend_report_payload = {
            "status": "ok",
            "summary": "Generated backend scaffold plan and endpoint inventory",
            "artifacts": created,
            "details": {
                "backend": backend,
                "database": database,
                "orm": orm,
                "entities": entities,
                "endpoint_count": len(endpoints),
            },
        }
        backend_report_path.write_text(json.dumps(backend_report_payload, indent=2), encoding="utf-8")

    artifacts = [str(report_path)]
    if not args.dry_run:
        artifacts = [str(openapi_path), str(backend_report_path), str(report_path)] + created

    result = {
        "status": "ok" if config_path else "warning",
        "summary": "Generated backend framework, ORM, and API contract plan",
        "artifacts": artifacts,
        "details": {
            "project_config_path": str(config_path) if config_path else "",
            "backend": backend,
            "database": database,
            "orm": orm,
            "entities": entities,
            "endpoint_count": len(endpoints),
            "endpoints": endpoints,
            "env_required": ["DATABASE_URL", "JWT_SECRET", "API_BASE_URL", "FILE_UPLOAD_BUCKET"],
            "dry_run": args.dry_run,
        },
    }
    render_result(result, report_path, args.format)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
