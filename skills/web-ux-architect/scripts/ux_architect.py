#!/usr/bin/env python3
"""
web-ux-architect script
Usage: python scripts/ux_architect.py --input <path> --output <path> --format json|md|csv [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DESIGN_TOOLS = [
    {"name": "Google Stitch", "url": "https://stitch.withgoogle.com/"},
    {"name": "Relume", "url": "https://relume.io/"},
    {"name": "v0 by Vercel", "url": "https://v0.dev/"},
    {"name": "Framer AI", "url": "https://framer.com/"},
    {"name": "Uizard", "url": "https://uizard.io/"},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate sitemap and wireframe specs from project config")
    parser.add_argument("--input", default=".", help="Path to workspace or config file")
    parser.add_argument("--output", default=".", help="Output file path or directory")
    parser.add_argument("--format", choices=["json", "md", "csv"], default="json")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_output_file(output_arg: str, fmt: str, stem: str) -> Path:
    out = Path(output_arg)
    if out.suffix.lower() in {".json", ".md", ".csv"}:
        return out
    return out / f"{stem}.{fmt}"


def locate_project_config(input_arg: str) -> Path | None:
    path = Path(input_arg)
    if path.is_file() and path.name == "project-config.json":
        return path
    if path.is_dir():
        config_path = path / "project-config.json"
        if config_path.exists():
            return config_path
    return None


def load_project_config(input_arg: str) -> tuple[dict[str, Any], Path | None]:
    config_path = locate_project_config(input_arg)
    if config_path is None:
        return {}, None
    return json.loads(config_path.read_text(encoding="utf-8")), config_path


def build_sitemap(project_type: str) -> list[dict[str, str]]:
    ptype = project_type.lower()
    if ptype == "portfolio":
        routes = [
            ("/", "Home"),
            ("/about", "About"),
            ("/projects", "Projects"),
            ("/projects/:slug", "Project detail"),
            ("/blog", "Blog"),
            ("/contact", "Contact"),
        ]
    elif ptype == "e-commerce":
        routes = [
            ("/", "Storefront"),
            ("/shop", "Product listing"),
            ("/product/:id", "Product detail"),
            ("/cart", "Cart"),
            ("/checkout", "Checkout"),
            ("/orders", "Orders"),
            ("/account", "Account"),
            ("/support", "Support"),
        ]
    elif ptype == "api-only":
        routes = [
            ("/docs", "Developer docs"),
            ("/status", "API status"),
            ("/changelog", "Release notes"),
            ("/auth", "Authentication guide"),
            ("/pricing", "API plans"),
        ]
    else:
        routes = [
            ("/", "Home"),
            ("/features", "Features"),
            ("/pricing", "Pricing"),
            ("/about", "About"),
            ("/login", "Login"),
            ("/signup", "Sign up"),
            ("/dashboard", "Dashboard"),
            ("/settings", "Settings"),
            ("/docs", "Documentation"),
            ("/contact", "Contact"),
        ]

    return [{"route": route, "name": name} for route, name in routes]


def build_wireframe_rows(sitemap: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for page in sitemap:
        route = page["route"]
        rows.append(
            {
                "route": route,
                "purpose": page["name"],
                "header": "Global nav, logo, primary CTA",
                "hero": "Page headline and supporting value prop",
                "content": f"Core content modules for {route}",
                "sidebar": "Optional contextual links / metadata",
                "footer": "Site links, legal links, contact",
            }
        )
    return rows


def render_sitemap_markdown(sitemap: list[dict[str, str]]) -> str:
    lines = ["# Sitemap", "", "| Route | Page |", "|---|---|"]
    for row in sitemap:
        lines.append(f"| {row['route']} | {row['name']} |")
    return "\n".join(lines) + "\n"


def render_wireframes_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Wireframes",
        "",
        "| Route | Purpose | Header | Hero | Content | Sidebar | Footer |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {route} | {purpose} | {header} | {hero} | {content} | {sidebar} | {footer} |".format(
                **row
            )
        )
    return "\n".join(lines) + "\n"


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
            f"- pages: {result['details']['page_count']}",
            "",
            "## Suggested Design Tools",
        ]
        lines.extend([f"- {tool['name']}: {tool['url']}" for tool in result["details"]["design_tools"]])
        output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        writer.writerow(["status", result["status"]])
        writer.writerow(["summary", result["summary"]])
        writer.writerow(["page_count", result["details"]["page_count"]])
        writer.writerow(["project_type", result["details"]["project_type"]])


def main() -> int:
    args = parse_args()
    config, config_path = load_project_config(args.input)
    project_type = str(config.get("project_type", "saas"))
    sitemap = build_sitemap(project_type)
    wireframes = build_wireframe_rows(sitemap)

    report_path = resolve_output_file(args.output, args.format, "ux-architect-report")
    output_root = report_path.parent
    sitemap_path = output_root / "sitemap.md"
    wireframes_path = output_root / "wireframes.md"
    ux_report_path = output_root / "ux-report.json"

    if not args.dry_run:
        sitemap_path.write_text(render_sitemap_markdown(sitemap), encoding="utf-8")
        wireframes_path.write_text(render_wireframes_markdown(wireframes), encoding="utf-8")
        ux_payload = {
            "status": "ok",
            "summary": "Generated sitemap and wireframes",
            "artifacts": [str(sitemap_path), str(wireframes_path)],
            "details": {"page_count": len(sitemap), "project_type": project_type},
        }
        ux_report_path.write_text(json.dumps(ux_payload, indent=2), encoding="utf-8")

    artifacts = [str(report_path)]
    if not args.dry_run:
        artifacts = [str(sitemap_path), str(wireframes_path), str(ux_report_path), str(report_path)]

    result = {
        "status": "ok" if config_path else "warning",
        "summary": "Generated UX architecture plan from project config",
        "artifacts": artifacts,
        "details": {
            "project_config_path": str(config_path) if config_path else "",
            "project_type": project_type,
            "page_count": len(sitemap),
            "sitemap": sitemap,
            "design_tools": DESIGN_TOOLS,
            "dry_run": args.dry_run,
        },
    }
    render_result(result, report_path, args.format)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
