#!/usr/bin/env python3
"""
web-frontend-designer script
Usage: python scripts/frontend_designer.py --input <path> --output <path> --format json|md|csv [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


FRAMEWORK_DEPS = {
    "next.js": ["next", "react", "react-dom"],
    "react": ["react", "react-dom", "vite"],
    "vue": ["vue", "vite"],
    "nuxt": ["nuxt", "vue"],
    "sveltekit": ["@sveltejs/kit", "svelte"],
    "angular": ["@angular/core", "@angular/router"],
    "astro": ["astro"],
    "plain html/css/js": [],
}
CSS_DEPS = {
    "tailwind css": ["tailwindcss", "postcss", "autoprefixer"],
    "shadcn/ui": ["tailwindcss", "class-variance-authority", "clsx", "tailwind-merge"],
    "chakra ui": ["@chakra-ui/react", "@emotion/react", "@emotion/styled", "framer-motion"],
    "material ui": ["@mui/material", "@emotion/react", "@emotion/styled"],
    "ant design": ["antd"],
    "mantine": ["@mantine/core", "@mantine/hooks"],
    "daisyui": ["tailwindcss", "daisyui"],
    "vanilla css": [],
}
ASSET_LIBRARIES = [
    "Font Awesome",
    "React Bits",
    "Spline",
    "Lucide",
    "Shadcn/ui",
    "Aceternity UI",
    "Magic UI",
    "Framer Motion",
    "React Three Fiber",
    "Google Fonts or Fontsource",
    "Unsplash API / Pexels / Lummi",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan and scaffold frontend implementation")
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


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_project_config(input_arg: str) -> tuple[dict[str, Any], Path | None]:
    path = Path(input_arg)
    if path.is_file():
        return read_json_if_exists(path), path
    config_path = path / "project-config.json"
    if config_path.exists():
        return read_json_if_exists(config_path), config_path
    return {}, None


def parse_sitemap(input_arg: str, project_type: str) -> list[str]:
    root = Path(input_arg)
    sitemap_path = root / "sitemap.md"
    routes: list[str] = []
    if sitemap_path.exists():
        for line in sitemap_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("| /"):
                cols = [item.strip() for item in line.split("|") if item.strip()]
                if cols:
                    route = cols[0]
                    if route not in routes:
                        routes.append(route)
    if routes:
        return routes
    if project_type == "portfolio":
        return ["/", "/about", "/projects", "/projects/:slug", "/blog", "/contact"]
    if project_type == "e-commerce":
        return ["/", "/shop", "/product/:id", "/cart", "/checkout", "/account"]
    return ["/", "/features", "/pricing", "/login", "/signup", "/dashboard", "/settings"]


def sanitize_route_to_file(route: str) -> str:
    cleaned = route.strip("/")
    if not cleaned:
        return "home"
    cleaned = cleaned.replace("/", "_").replace(":", "")
    return cleaned


def resolve_next_app_page_file(route_root: Path, route: str) -> Path:
    segments = [segment for segment in route.strip("/").split("/") if segment]
    if not segments:
        return route_root / "page.tsx"

    normalized_segments: list[str] = []
    for segment in segments:
        if segment.startswith(":") and len(segment) > 1:
            normalized_segments.append(f"[{segment[1:]}]")
        else:
            normalized_segments.append(segment)
    return route_root.joinpath(*normalized_segments) / "page.tsx"


def scaffold_frontend(frontend_root: Path, routes: list[str], framework: str) -> list[str]:
    created: list[str] = []
    dirs = [frontend_root / "components", frontend_root / "layouts", frontend_root / "public"]
    if framework == "next.js":
        dirs.append(frontend_root / "app")
    else:
        dirs.append(frontend_root / "pages")

    for dpath in dirs:
        dpath.mkdir(parents=True, exist_ok=True)
        created.append(str(dpath))

    route_root = frontend_root / ("app" if framework == "next.js" else "pages")
    if framework == "next.js":
        layout_file = route_root / "layout.tsx"
        layout_file.write_text(
            "\n".join(
                [
                    "import type { ReactNode } from \"react\";",
                    "",
                    "export default function RootLayout({ children }: { children: ReactNode }) {",
                    "  return (",
                    "    <html lang=\"en\">",
                    "      <body>{children}</body>",
                    "    </html>",
                    "  );",
                    "}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        created.append(str(layout_file))

    for route in routes:
        if framework == "next.js":
            page_file = resolve_next_app_page_file(route_root, route)
        else:
            filename = sanitize_route_to_file(route)
            page_file = route_root / f"{filename}.tsx"
        page_file.parent.mkdir(parents=True, exist_ok=True)
        page_file.write_text(
            "\n".join(
                [
                    "export default function Page() {",
                    f"  return <main aria-label=\"{route} page\">{route} placeholder</main>;",
                    "}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        created.append(str(page_file))

    component_file = frontend_root / "components" / "SiteHeader.tsx"
    component_file.write_text(
        "\n".join(
            [
                "export function SiteHeader() {",
                "  return <header aria-label=\"Site header\">Navigation</header>;",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    created.append(str(component_file))
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
            f"- framework: {result['details']['framework']}",
            f"- routes: {result['details']['route_count']}",
            "",
            "## Planned Libraries",
        ]
        lines.extend([f"- {item}" for item in result["details"]["asset_libraries"]])
        output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    with output_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        writer.writerow(["status", result["status"]])
        writer.writerow(["framework", result["details"]["framework"]])
        writer.writerow(["css_system", result["details"]["css_system"]])
        writer.writerow(["route_count", result["details"]["route_count"]])


def main() -> int:
    args = parse_args()
    config, config_path = load_project_config(args.input)
    stack = config.get("stack", {}) if isinstance(config.get("stack"), dict) else {}
    framework = str(stack.get("frontend", "next.js")).lower()
    css_system = str(stack.get("css_system", "tailwind css")).lower()
    project_type = str(config.get("project_type", "saas")).lower()
    routes = parse_sitemap(args.input, project_type)

    deps = sorted(set(FRAMEWORK_DEPS.get(framework, []) + CSS_DEPS.get(css_system, [])))
    component_tree = {
        "root": "frontend",
        "folders": ["components", "layouts", "public", "app" if framework == "next.js" else "pages"],
        "routes": routes,
    }

    report_path = resolve_output_file(args.output, args.format, "frontend-designer-report")
    output_root = report_path.parent
    frontend_root = output_root / "frontend"
    frontend_report = output_root / "frontend-report.json"

    created_paths: list[str] = []
    if not args.dry_run:
        created_paths = scaffold_frontend(frontend_root, routes, framework)
        frontend_report_payload = {
            "status": "ok",
            "summary": "Scaffolded frontend placeholders and dependencies",
            "artifacts": created_paths,
            "details": {
                "framework": framework,
                "css_system": css_system,
                "dependencies": deps,
                "route_count": len(routes),
            },
        }
        frontend_report.write_text(json.dumps(frontend_report_payload, indent=2), encoding="utf-8")

    artifacts = [str(report_path)]
    if not args.dry_run:
        artifacts = [str(frontend_report), str(report_path)] + created_paths

    result = {
        "status": "ok" if config_path else "warning",
        "summary": "Generated frontend scaffold plan and dependency inventory",
        "artifacts": artifacts,
        "details": {
            "project_config_path": str(config_path) if config_path else "",
            "framework": framework,
            "css_system": css_system,
            "dependencies": deps,
            "asset_libraries": ASSET_LIBRARIES,
            "component_tree": component_tree,
            "responsive_mobile_first": True,
            "dark_mode": True,
            "a11y_aria_required": True,
            "route_count": len(routes),
            "dry_run": args.dry_run,
        },
    }
    render_result(result, report_path, args.format)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
