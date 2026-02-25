#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import stat
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
    return sorted([path for path in skills_dir.iterdir() if path.is_dir() and (path / "SKILL.md").exists()])


def is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    st = path.lstat()
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(st, "st_file_attributes", 0) & reparse_flag)


def iter_skill_files(skill_dir: Path) -> list[Path]:
    collected: list[Path] = []
    for root, dirs, files in os.walk(skill_dir, followlinks=False):
        root_path = Path(root)

        blocked_dirs = []
        safe_dirs = []
        for name in dirs:
            child = root_path / name
            if is_link_or_reparse(child):
                blocked_dirs.append(str(child))
            else:
                safe_dirs.append(name)
        if blocked_dirs:
            raise ValueError(
                "Refusing to package symlink/reparse directories: "
                + ", ".join(blocked_dirs)
            )
        dirs[:] = safe_dirs

        for name in files:
            child = root_path / name
            if is_link_or_reparse(child):
                raise ValueError(
                    f"Refusing to package symlink/reparse file: {child}"
                )
            collected.append(child)

    return sorted(collected)


def create_zip(skill_dir: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{skill_dir.name}.zip"
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for path in iter_skill_files(skill_dir):
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
    try:
        for skill_dir in skill_dirs:
            built.append(create_zip(skill_dir, output_dir))
    except ValueError as exc:
        print(f"Packaging aborted: {exc}")
        return 1

    print(f"Packaged {len(built)} skills to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
