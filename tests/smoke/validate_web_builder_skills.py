#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"
WEB_SKILLS = [
    "web-stack-planner",
    "web-ux-architect",
    "web-frontend-designer",
    "web-backend-builder",
    "web-auth-integrator",
    "web-database-validator",
    "web-api-tester",
    "web-frontend-tester",
    "web-security-auditor",
    "web-deploy-launcher",
]
CLAUDE_DESCRIPTION_LIMIT = 200


def parse_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        raise AssertionError(f"{path}: invalid or missing YAML frontmatter")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise AssertionError(f"{path}: frontmatter must parse to a mapping")
    return data


def main() -> int:
    failures: list[str] = []

    for skill_name in WEB_SKILLS:
        skill_dir = SKILLS_DIR / skill_name
        if not skill_dir.exists():
            failures.append(f"{skill_name}: directory missing")
            continue

        skill_md = skill_dir / "SKILL.md"
        openai_yaml = skill_dir / "agents" / "openai.yaml"
        scripts_dir = skill_dir / "scripts"

        if not skill_md.exists():
            failures.append(f"{skill_name}: missing SKILL.md")
            continue
        if not openai_yaml.exists():
            failures.append(f"{skill_name}: missing agents/openai.yaml")
            continue
        if not scripts_dir.exists():
            failures.append(f"{skill_name}: missing scripts directory")
            continue
        if not list(scripts_dir.glob("*.py")):
            failures.append(f"{skill_name}: scripts directory has no python files")
            continue

        try:
            frontmatter = parse_frontmatter(skill_md)
        except Exception as exc:
            failures.append(str(exc))
            continue

        if frontmatter.get("name") != skill_name:
            failures.append(f"{skill_name}: frontmatter name must match folder name")

        description = frontmatter.get("description")
        if not isinstance(description, str) or not description.strip():
            failures.append(f"{skill_name}: frontmatter description must be non-empty")
        elif len(description.strip()) > CLAUDE_DESCRIPTION_LIMIT:
            failures.append(
                f"{skill_name}: frontmatter description exceeds {CLAUDE_DESCRIPTION_LIMIT} chars"
            )

        try:
            openai_data = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            failures.append(f"{skill_name}: invalid YAML in openai.yaml ({exc})")
            continue
        if not isinstance(openai_data, dict):
            failures.append(f"{skill_name}: openai.yaml must be a mapping")
            continue

        interface = openai_data.get("interface")
        if not isinstance(interface, dict):
            failures.append(f"{skill_name}: openai.yaml missing interface mapping")
            continue

        for key in ("display_name", "short_description", "default_prompt"):
            value = interface.get(key)
            if not isinstance(value, str) or not value.strip():
                failures.append(f"{skill_name}: interface.{key} is required")

    if failures:
        print("web-builder smoke validation failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Validated {len(WEB_SKILLS)} web-builder skills successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
