#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

MAX_INPUT_BYTES = 1_048_576


CATEGORY_NOTES = {
    "cybersecurity": "Focus on defensive and tooling-centric workflows. Exclude exploit payload guidance.",
    "ml": "Focus on reproducibility, experiment tracking, and measurable evaluation criteria.",
    "agentic": "Focus on workflow orchestration, MCP integration, and deterministic fallbacks.",
    "workspace": "Focus on Google API auth boundaries, quotas, and human-readable audit output.",
    "general": "Focus on concrete triggers, deterministic scripts, and concise references.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a category-specific skill starter.")
    parser.add_argument("--input", required=False, help="Path to JSON input.")
    parser.add_argument("--output", required=True, help="Path to output file.")
    parser.add_argument("--format", choices=["json", "md", "csv"], default="json")
    parser.add_argument("--dry-run", action="store_true", help="Plan actions without file writes.")
    parser.add_argument(
        "--target-dir",
        required=False,
        help="Directory where skill scaffold should be created when dry-run is disabled.",
    )
    parser.add_argument(
        "--allow-outside-workspace",
        action="store_true",
        help="Allow --target-dir to resolve outside the current workspace.",
    )
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


def normalize_name(raw: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in raw.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")


def resolve_path_in_workspace(
    raw_path: Path,
    workspace_root: Path,
    label: str,
    allow_outside_workspace: bool,
) -> Path:
    resolved = raw_path.resolve()
    if allow_outside_workspace:
        return resolved
    try:
        resolved.relative_to(workspace_root)
    except ValueError as exc:
        raise ValueError(
            f"{label} must be inside workspace root: {workspace_root}"
        ) from exc
    return resolved


def build_skill_md(skill_name: str, description: str, note: str) -> str:
    title = " ".join(part.capitalize() for part in skill_name.split("-"))
    return f"""---
name: {skill_name}
description: {description}
---

# {title}

## Overview

Use this skill for repeatable {skill_name} tasks.

## Category Note

{note}
"""


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
            f"- artifacts: {len(result['artifacts'])}",
            "",
            "## Details",
        ]
        for key, value in result["details"].items():
            lines.append(f"- {key}: {value}")
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["key", "value"])
        writer.writerow(["status", result["status"]])
        writer.writerow(["summary", result["summary"]])
        writer.writerow(["artifacts_count", str(len(result["artifacts"]))])
        for key, value in result["details"].items():
            writer.writerow([key, json.dumps(value) if isinstance(value, (dict, list)) else value])


def maybe_scaffold(
    skill_name: str,
    description: str,
    note: str,
    target_dir: Path | None,
    dry_run: bool,
    workspace_root: Path,
    allow_outside_workspace: bool,
) -> list[str]:
    artifacts: list[str] = []
    if target_dir is None:
        return artifacts

    safe_target_dir = resolve_path_in_workspace(
        target_dir,
        workspace_root,
        "target_dir",
        allow_outside_workspace,
    )
    skill_dir = safe_target_dir / skill_name
    artifacts.extend(
        [
            str(skill_dir / "SKILL.md"),
            str(skill_dir / "agents" / "openai.yaml"),
            str(skill_dir / "scripts"),
            str(skill_dir / "references"),
            str(skill_dir / "assets"),
        ]
    )

    if dry_run:
        return artifacts

    (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(parents=True, exist_ok=True)
    (skill_dir / "assets").mkdir(parents=True, exist_ok=True)

    (skill_dir / "SKILL.md").write_text(
        build_skill_md(skill_name, description, note),
        encoding="utf-8",
    )
    (skill_dir / "agents" / "openai.yaml").write_text(
        "\n".join(
            [
                "interface:",
                f"  display_name: \"{' '.join(part.capitalize() for part in skill_name.split('-'))}\"",
                "  short_description: \"Starter metadata for new skill scaffolding\"",
                f"  default_prompt: \"Use ${skill_name} to implement this starter skill.\"",
                "",
            ]
        ),
        encoding="utf-8",
    )

    return artifacts


def main() -> int:
    args = parse_args()
    payload = load_input(args.input)
    workspace_root = Path.cwd().resolve()
    raw_name = payload.get("skill_name", "new-skill")
    skill_name = normalize_name(raw_name) or "new-skill"
    category = str(payload.get("category", "general")).lower().strip()
    description = str(
        payload.get(
            "description",
            f"Create and execute workflows for {skill_name}. Use when agents need structured guidance.",
        )
    ).strip()

    note = CATEGORY_NOTES.get(category, CATEGORY_NOTES["general"])
    target_dir = Path(args.target_dir) if args.target_dir else None
    artifacts = maybe_scaffold(
        skill_name,
        description,
        note,
        target_dir,
        args.dry_run,
        workspace_root,
        args.allow_outside_workspace,
    )

    result = {
        "status": "ok",
        "summary": f"Generated starter plan for '{skill_name}'",
        "artifacts": artifacts,
        "details": {
            "skill_name": skill_name,
            "category": category,
            "description": description,
            "note": note,
            "scaffolded": bool(target_dir and not args.dry_run),
        },
    }

    write_output(result, Path(args.output), args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
