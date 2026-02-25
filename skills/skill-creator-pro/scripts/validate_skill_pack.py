#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import yaml

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
MAX_INPUT_BYTES = 1_048_576
ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "allowed-tools",
    "metadata",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a repository of skills.")
    parser.add_argument("--input", required=False, help="Optional JSON input with skill_root.")
    parser.add_argument("--output", required=True, help="Path to output file.")
    parser.add_argument("--format", choices=["json", "md", "csv"], default="json")
    parser.add_argument("--dry-run", action="store_true", help="Retained for contract consistency.")
    return parser.parse_args()


def load_input(path: str | None, max_input_bytes: int = MAX_INPUT_BYTES) -> dict:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    if p.stat().st_size > max_input_bytes:
        raise ValueError(f"Input file exceeds {max_input_bytes} bytes: {p}")
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

    unexpected = set(frontmatter.keys()) - ALLOWED_FRONTMATTER_KEYS
    if unexpected:
        errors.append(
            f"{skill_name}: unsupported frontmatter keys: {', '.join(sorted(unexpected))}"
        )

    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"{skill_name}: frontmatter name must be a non-empty string")
    else:
        name = name.strip()
        if name != skill_name:
            errors.append(f"{skill_name}: frontmatter name must match skill directory")
        if len(name) > MAX_NAME_LENGTH:
            errors.append(f"{skill_name}: frontmatter name exceeds {MAX_NAME_LENGTH} chars")
        if not re.match(r"^[a-z0-9-]+$", name):
            errors.append(
                f"{skill_name}: frontmatter name must be lowercase hyphen-case with digits"
            )
        if name.startswith("-") or name.endswith("-") or "--" in name:
            errors.append(f"{skill_name}: frontmatter name has invalid hyphen placement")

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{skill_name}: frontmatter description must be a non-empty string")
    elif len(description.strip()) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"{skill_name}: frontmatter description exceeds {MAX_DESCRIPTION_LENGTH} chars"
        )

    compatibility = frontmatter.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str) or not compatibility.strip():
            errors.append(
                f"{skill_name}: compatibility must be a non-empty string when provided"
            )
        elif len(compatibility.strip()) > MAX_COMPATIBILITY_LENGTH:
            errors.append(
                f"{skill_name}: compatibility exceeds {MAX_COMPATIBILITY_LENGTH} chars"
            )

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
            short_description = interface.get("short_description")
            if isinstance(short_description, str):
                length = len(short_description.strip())
                if length < 25 or length > 64:
                    errors.append(
                        f"{skill_name}: interface.short_description must be 25-64 chars"
                    )
            elif short_description is not None:
                errors.append(f"{skill_name}: interface.short_description must be a string")

            default_prompt = interface.get("default_prompt")
            if isinstance(default_prompt, str):
                if f"${skill_name}" not in default_prompt:
                    errors.append(
                        f"{skill_name}: interface.default_prompt must mention ${skill_name}"
                    )
            elif default_prompt is not None:
                errors.append(f"{skill_name}: interface.default_prompt must be a string")

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


def is_candidate_skill_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    if (path / "SKILL.md").exists():
        return True
    if (path / "agents" / "openai.yaml").exists():
        return True
    scripts_dir = path / "scripts"
    if scripts_dir.exists() and any(scripts_dir.glob("*.py")):
        return True
    return False


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
    skill_dirs = sorted([path for path in skill_root.iterdir() if is_candidate_skill_dir(path)])
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
