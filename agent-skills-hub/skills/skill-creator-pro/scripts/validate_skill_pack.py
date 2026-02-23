#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a repository of skills.")
    parser.add_argument("--input", required=False, help="Optional JSON input with skill_root.")
    parser.add_argument("--output", required=True, help="Path to output file.")
    parser.add_argument("--format", choices=["json", "md", "csv"], default="json")
    parser.add_argument("--dry-run", action="store_true", help="Retained for contract consistency.")
    return parser.parse_args()


def load_input(path: str | None) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def parse_frontmatter(content: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        raise ValueError("Missing or invalid YAML frontmatter")
    parsed = yaml.safe_load(match.group(1))
    if not isinstance(parsed, dict):
        raise ValueError("Frontmatter must be a YAML object")
    return parsed


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_name = skill_dir.name

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_name}: missing SKILL.md"]

    try:
        frontmatter = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{skill_name}: invalid SKILL.md frontmatter ({exc})"]

    for required_key in ("name", "description"):
        if required_key not in frontmatter:
            errors.append(f"{skill_name}: missing frontmatter key '{required_key}'")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        errors.append(f"{skill_name}: missing agents/openai.yaml")
    else:
        data = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
        interface = data.get("interface") if isinstance(data, dict) else None
        if not isinstance(interface, dict):
            errors.append(f"{skill_name}: invalid interface mapping in openai.yaml")
        else:
            for required_key in ("display_name", "short_description", "default_prompt"):
                if required_key not in interface:
                    errors.append(f"{skill_name}: missing interface.{required_key}")

    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists() or not list(scripts_dir.glob("*.py")):
        errors.append(f"{skill_name}: scripts directory missing .py files")

    return errors


def write_output(result: dict, output_path: Path, fmt: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return

    if fmt == "md":
        lines = [
            f"# {result['summary']}",
            "",
            f"- status: {result['status']}",
            f"- skills_checked: {result['details']['skills_checked']}",
            f"- error_count: {len(result['details']['errors'])}",
            "",
        ]
        if result["details"]["errors"]:
            lines.append("## Errors")
            for err in result["details"]["errors"]:
                lines.append(f"- {err}")
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        writer.writerow(["status", result["status"]])
        writer.writerow(["summary", result["summary"]])
        writer.writerow(["skills_checked", str(result["details"]["skills_checked"])])
        for err in result["details"]["errors"]:
            writer.writerow(["error", err])


def main() -> int:
    args = parse_args()
    payload = load_input(args.input)
    skill_root = Path(payload.get("skill_root", "skills")).resolve()

    if not skill_root.exists():
        result = {
            "status": "error",
            "summary": f"Skill root not found: {skill_root}",
            "artifacts": [],
            "details": {"skills_checked": 0, "errors": [f"Missing path: {skill_root}"]},
        }
        write_output(result, Path(args.output), args.format)
        return 1

    errors: list[str] = []
    skill_dirs = sorted([path for path in skill_root.iterdir() if path.is_dir()])
    for skill_dir in skill_dirs:
        errors.extend(validate_skill(skill_dir))

    status = "ok" if not errors else "error"
    result = {
        "status": status,
        "summary": f"Validated {len(skill_dirs)} skill directories",
        "artifacts": [],
        "details": {
            "skills_checked": len(skill_dirs),
            "errors": errors,
            "dry_run": args.dry_run,
        },
    }
    write_output(result, Path(args.output), args.format)
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
