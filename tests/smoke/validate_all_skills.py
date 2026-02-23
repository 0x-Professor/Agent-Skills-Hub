#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"
TOOLS_DIR = ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from quick_validate import validate_skill  # noqa: E402


def validate_openai_yaml(skill_dir: Path, skill_name: str) -> list[str]:
    errors: list[str] = []
    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        return [f"{skill_name}: missing agents/openai.yaml"]

    data = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return [f"{skill_name}: agents/openai.yaml must be a mapping"]

    interface = data.get("interface")
    if not isinstance(interface, dict):
        return [f"{skill_name}: missing interface mapping in openai.yaml"]

    display_name = interface.get("display_name")
    short_description = interface.get("short_description")
    default_prompt = interface.get("default_prompt")

    if not isinstance(display_name, str) or not display_name.strip():
        errors.append(f"{skill_name}: interface.display_name is required")

    if not isinstance(short_description, str):
        errors.append(f"{skill_name}: interface.short_description is required")
    else:
        ln = len(short_description.strip())
        if ln < 25 or ln > 64:
            errors.append(
                f"{skill_name}: interface.short_description must be 25-64 chars (got {ln})"
            )

    if not isinstance(default_prompt, str) or not default_prompt.strip():
        errors.append(f"{skill_name}: interface.default_prompt is required")
    elif f"${skill_name}" not in default_prompt:
        errors.append(
            f"{skill_name}: interface.default_prompt must explicitly mention ${skill_name}"
        )

    return errors


def validate_scripts_dir(skill_dir: Path, skill_name: str) -> list[str]:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return [f"{skill_name}: missing scripts directory"]
    py_scripts = list(scripts_dir.glob("*.py"))
    if not py_scripts:
        return [f"{skill_name}: scripts directory must contain at least one .py file"]
    return []


def main() -> int:
    if not SKILLS_DIR.exists():
        print(f"Skills directory not found: {SKILLS_DIR}")
        return 1

    errors: list[str] = []
    skill_dirs = sorted([p for p in SKILLS_DIR.iterdir() if p.is_dir()])
    if not skill_dirs:
        print("No skills found.")
        return 1

    for skill_dir in skill_dirs:
        skill_name = skill_dir.name
        valid, msg = validate_skill(skill_dir)
        if not valid:
            errors.append(f"{skill_name}: {msg}")
            continue

        errors.extend(validate_openai_yaml(skill_dir, skill_name))
        errors.extend(validate_scripts_dir(skill_dir, skill_name))

    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"- {err}")
        return 1

    print(f"Validated {len(skill_dirs)} skills successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
