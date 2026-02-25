#!/usr/bin/env python3
from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"


def load_skills_ref():
    try:
        return importlib.import_module("skills_ref")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "skills_ref package is required for Agent Skills reference checks. "
            "Install with: python -m pip install skills-ref"
        ) from exc


def assert_zip_structure(output_dir: Path) -> dict:
    package_script = ROOT / "tools" / "package_skills_for_claude.py"
    if not package_script.exists():
        raise RuntimeError("Missing packaging helper: tools/package_skills_for_claude.py")

    output_dir.mkdir(parents=True, exist_ok=True)
    rc = subprocess.run(
        [
            sys.executable,
            str(package_script),
            "--skills-dir",
            str(SKILLS_DIR),
            "--output",
            str(output_dir),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    if rc.returncode != 0:
        raise RuntimeError(
            "Failed to package skills for Claude uploads\n"
            f"stdout={rc.stdout}\nstderr={rc.stderr}"
        )

    zip_files = sorted(output_dir.glob("*.zip"))
    expected_skill_dirs = [
        p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists()
    ]
    if len(zip_files) != len(expected_skill_dirs):
        raise RuntimeError("Unexpected zip count from package_skills_for_claude.py")

    for zip_file in zip_files:
        skill_name = zip_file.stem
        with ZipFile(zip_file, "r") as zf:
            members = set(zf.namelist())
            expected = f"{skill_name}/SKILL.md"
            if expected not in members:
                raise RuntimeError(f"{zip_file.name}: missing {expected} at zip root")

    return {"zip_count": len(zip_files)}


def main() -> int:
    skills_ref = load_skills_ref()
    skill_paths = sorted(
        [path for path in SKILLS_DIR.iterdir() if path.is_dir() and (path / "SKILL.md").exists()]
    )
    if not skill_paths:
        raise RuntimeError("No skills found for Agent Skills reference checks")

    validate = getattr(skills_ref, "validate", None)
    read_properties = getattr(skills_ref, "read_properties", None)
    to_prompt = getattr(skills_ref, "to_prompt", None)
    if not callable(validate) or not callable(read_properties) or not callable(to_prompt):
        raise RuntimeError(
            "skills_ref API mismatch. Expected validate(), read_properties(), and to_prompt()."
        )

    validation_errors: dict[str, list[str]] = {}
    for skill_path in skill_paths:
        errors = validate(skill_path)
        if errors:
            validation_errors[skill_path.name] = [str(err) for err in errors]

        props = read_properties(skill_path)
        skill_name = getattr(props, "name", None)
        description = getattr(props, "description", None)

        if not isinstance(skill_name, str):
            raise RuntimeError(f"{skill_path.name}: read_properties().name must be a string")
        if skill_name != skill_path.name:
            raise RuntimeError(
                f"{skill_path.name}: read_properties().name must match skill folder name"
            )
        if not isinstance(description, str) or not description.strip():
            raise RuntimeError(f"{skill_path.name}: empty description from read_properties()")

    if validation_errors:
        raise RuntimeError(f"skills_ref.validate errors: {json.dumps(validation_errors, indent=2)}")

    prompt_xml = to_prompt(skill_paths)
    if "<available_skills>" not in prompt_xml:
        raise RuntimeError("skills_ref.to_prompt output missing <available_skills> root")
    for skill_path in skill_paths:
        pattern = rf"<name>\s*{re.escape(skill_path.name)}\s*</name>"
        if not re.search(pattern, prompt_xml):
            raise RuntimeError(
                f"skills_ref.to_prompt output missing skill name entry: {skill_path.name}"
            )
        expected_location = str((skill_path / "SKILL.md").resolve())
        if expected_location not in prompt_xml:
            raise RuntimeError(
                f"skills_ref.to_prompt output missing SKILL.md location for {skill_path.name}"
            )

    with tempfile.TemporaryDirectory() as tmp:
        packaging_summary = assert_zip_structure(Path(tmp) / "claude-zips")

    summary = {
        "status": "ok",
        "skills_checked": len(skill_paths),
        "prompt_xml_bytes": len(prompt_xml.encode("utf-8")),
        "packaging": packaging_summary,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"Agent Skills reference check failure: {exc}")
        raise SystemExit(1)
