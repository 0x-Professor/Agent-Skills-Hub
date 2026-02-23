#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Package each skill directory as a Claude.ai-compatible zip."
    )
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="Directory containing skill folders (default: skills).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for generated zip files.",
    )
    return parser.parse_args()


def iter_skill_dirs(skills_dir: Path) -> list[Path]:
    return sorted([path for path in skills_dir.iterdir() if path.is_dir()])


def create_zip(skill_dir: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{skill_dir.name}.zip"
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for path in sorted(skill_dir.rglob("*")):
            if path.is_dir():
                continue
            rel_inside_skill = path.relative_to(skill_dir)
            archive_name = Path(skill_dir.name) / rel_inside_skill
            zf.write(path, archive_name.as_posix())
    return zip_path


def main() -> int:
    args = parse_args()
    skills_dir = Path(args.skills_dir).resolve()
    output_dir = Path(args.output).resolve()

    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}")
        return 1

    skill_dirs = iter_skill_dirs(skills_dir)
    if not skill_dirs:
        print(f"No skills found in: {skills_dir}")
        return 1

    built = []
    for skill_dir in skill_dirs:
        built.append(create_zip(skill_dir, output_dir))

    print(f"Packaged {len(built)} skills to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
