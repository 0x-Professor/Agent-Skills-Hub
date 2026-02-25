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

CLAUDE_DESCRIPTION_LIMIT = 200
MAX_COMPATIBILITY_LENGTH = 500


def parse_frontmatter(skill_dir: Path) -> tuple[dict | None, str | None]:
    skill_md = skill_dir / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    if "[TODO" in content or "TODO:" in content:
        return None, "contains TODO placeholder text"

    chunks = content.split("---", 2)
    if len(chunks) < 3:
        return None, "invalid frontmatter delimiter layout"

    try:
        data = yaml.safe_load(chunks[1])
    except yaml.YAMLError as exc:
        return None, f"invalid YAML frontmatter ({exc})"
    if not isinstance(data, dict):
        return None, "frontmatter must be a mapping"
    return data, None


def validate_frontmatter_portability(skill_dir: Path, skill_name: str) -> list[str]:
    errors: list[str] = []
    frontmatter, parse_error = parse_frontmatter(skill_dir)
    if parse_error:
        return [f"{skill_name}: {parse_error}"]

    assert frontmatter is not None
    name_value = frontmatter.get("name")
    description_value = frontmatter.get("description")
    if name_value != skill_name:
        errors.append(f"{skill_name}: frontmatter name must match folder name")

    if not isinstance(description_value, str):
        errors.append(f"{skill_name}: frontmatter description must be a string")
    else:
        desc_len = len(description_value.strip())
        if desc_len == 0:
            errors.append(f"{skill_name}: frontmatter description cannot be empty")
        if desc_len > CLAUDE_DESCRIPTION_LIMIT:
            errors.append(
                f"{skill_name}: frontmatter description exceeds {CLAUDE_DESCRIPTION_LIMIT} chars "
                f"(got {desc_len})"
            )

    compatibility_value = frontmatter.get("compatibility")
    if compatibility_value is not None:
        if not isinstance(compatibility_value, str):
            errors.append(f"{skill_name}: compatibility must be a string when provided")
        else:
            comp_len = len(compatibility_value.strip())
            if comp_len == 0:
                errors.append(f"{skill_name}: compatibility cannot be empty when provided")
            if comp_len > MAX_COMPATIBILITY_LENGTH:
                errors.append(
                    f"{skill_name}: compatibility exceeds {MAX_COMPATIBILITY_LENGTH} chars "
                    f"(got {comp_len})"
                )

    return errors


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
    skill_dirs = sorted([p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists()])
    if not skill_dirs:
        print("No skills found.")
        return 1

    for skill_dir in skill_dirs:
        skill_name = skill_dir.name
        valid, msg = validate_skill(skill_dir)
        if not valid:
            errors.append(f"{skill_name}: {msg}")
            continue

        errors.extend(validate_frontmatter_portability(skill_dir, skill_name))
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
