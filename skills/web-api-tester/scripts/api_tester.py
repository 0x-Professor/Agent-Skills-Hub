#!/usr/bin/env python3
"""
web-api-tester script
Usage: python scripts/api_tester.py --input <path> --output <path> --format json|md|csv [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate API testing matrix from openapi.yaml")
    parser.add_argument("--input", default=".", help="Path to workspace containing openapi.yaml")
    parser.add_argument("--output", default=".", help="Output file path or directory")
    parser.add_argument("--format", choices=["json", "md", "csv"], default="json")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_output_file(output_arg: str, fmt: str, stem: str) -> Path:
    out = Path(output_arg)
    if out.suffix.lower() in {".json", ".md", ".csv"}:
        return out
    return out / f"{stem}.{fmt}"


def locate_openapi(input_arg: str) -> Path | None:
    base = Path(input_arg)
    if base.is_file() and base.name.endswith((".yaml", ".yml")):
        return base
    for candidate in ("openapi.yaml", "openapi.yml"):
        candidate_path = base / candidate
        if candidate_path.exists():
            return candidate_path
    return None


def parse_openapi_paths(openapi_path: Path) -> list[dict[str, str]]:
    endpoints: list[dict[str, str]] = []
    current_path = ""
    for line in openapi_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if line.startswith("  /") and stripped.endswith(":"):
            current_path = stripped[:-1]
            continue
        if current_path and line.startswith("    ") and stripped.endswith(":"):
            method = stripped[:-1].lower()
            if method in HTTP_METHODS:
                endpoints.append({"method": method.upper(), "path": current_path})
    return endpoints


def build_test_cases(endpoints: list[dict[str, str]]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for endpoint in endpoints:
        key = f"{endpoint['method']} {endpoint['path']}"
        cases.extend(
            [
                {"endpoint": key, "scenario": "happy_path", "expected": "2xx"},
                {"endpoint": key, "scenario": "empty_or_missing_fields", "expected": "4xx"},
                {"endpoint": key, "scenario": "invalid_types", "expected": "4xx"},
                {"endpoint": key, "scenario": "unauthenticated", "expected": "401"},
                {"endpoint": key, "scenario": "wrong_role", "expected": "403"},
                {"endpoint": key, "scenario": "rate_limit", "expected": "429 or configured behavior"},
            ]
        )
    return cases


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
            f"- endpoints: {result['details']['endpoint_count']}",
            f"- test_cases: {result['details']['test_case_count']}",
            "",
            "## Coverage",
            f"- endpoint_coverage_pct: {result['details']['coverage']['endpoint_coverage_pct']}",
            f"- edge_case_coverage_pct: {result['details']['coverage']['edge_case_coverage_pct']}",
        ]
        output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        writer.writerow(["status", result["status"]])
        writer.writerow(["endpoint_count", result["details"]["endpoint_count"]])
        writer.writerow(["test_case_count", result["details"]["test_case_count"]])
        writer.writerow(["endpoint_coverage_pct", result["details"]["coverage"]["endpoint_coverage_pct"]])
        writer.writerow(["edge_case_coverage_pct", result["details"]["coverage"]["edge_case_coverage_pct"]])


def main() -> int:
    args = parse_args()
    openapi_path = locate_openapi(args.input)
    endpoints = parse_openapi_paths(openapi_path) if openapi_path else []
    test_cases = build_test_cases(endpoints)

    endpoint_coverage = 100 if endpoints else 0
    edge_coverage = 100 if endpoints else 0
    status = "ok" if endpoints else "warning"

    report_path = resolve_output_file(args.output, args.format, "api-tester-report")
    output_root = report_path.parent
    api_report_path = output_root / "api-test-report.json"
    test_matrix_path = output_root / "api-test-cases.json"

    if not args.dry_run:
        test_matrix_path.write_text(json.dumps(test_cases, indent=2), encoding="utf-8")
        api_report_payload = {
            "status": status,
            "summary": "API endpoint testing plan generated",
            "artifacts": [str(test_matrix_path)],
            "details": {
                "endpoint_count": len(endpoints),
                "test_case_count": len(test_cases),
                "coverage": {
                    "endpoint_coverage_pct": endpoint_coverage,
                    "edge_case_coverage_pct": edge_coverage,
                },
            },
        }
        api_report_path.write_text(json.dumps(api_report_payload, indent=2), encoding="utf-8")

    artifacts = [str(report_path)]
    if not args.dry_run:
        artifacts = [str(api_report_path), str(test_matrix_path), str(report_path)]

    result = {
        "status": status,
        "summary": "Generated API test coverage plan from OpenAPI contract",
        "artifacts": artifacts,
        "details": {
            "openapi_path": str(openapi_path) if openapi_path else "",
            "endpoint_count": len(endpoints),
            "test_case_count": len(test_cases),
            "coverage": {
                "endpoint_coverage_pct": endpoint_coverage,
                "edge_case_coverage_pct": edge_coverage,
            },
            "contract_validation": "Zod (TS) or Pydantic (Python)",
            "collection_tools": ["Bruno", "Hoppscotch"],
            "dry_run": args.dry_run,
        },
    }
    render_result(result, report_path, args.format)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
