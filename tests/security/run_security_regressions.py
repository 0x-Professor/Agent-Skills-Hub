#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAX_INPUT_BYTES = 1_048_576


class SecurityTestError(RuntimeError):
    pass


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=False,
        capture_output=True,
        text=True,
    )


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def assert_fails_with(proc: subprocess.CompletedProcess[str], expected_text: str, label: str) -> None:
    if proc.returncode == 0:
        raise SecurityTestError(f"{label}: expected failure but command succeeded")
    merged = f"{proc.stdout}\n{proc.stderr}"
    if expected_text not in merged:
        raise SecurityTestError(
            f"{label}: expected text '{expected_text}' not found\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )


def test_scaffold_root_boundary() -> str:
    script = ROOT / "skills" / "agentic-mcp-server-builder" / "scripts" / "scaffold_mcp_server.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        input_path = tmpdir / "input.json"
        output_path = tmpdir / "output.json"
        write_json(
            input_path,
            {
                "server_name": "ops-helper",
                "scaffold_root": "../outside-workspace",
                "tools": [{"name": "list", "description": "list incidents"}],
            },
        )
        proc = run(
            [
                sys.executable,
                str(script),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--format",
                "json",
                "--dry-run",
            ],
            cwd=ROOT,
        )
        assert_fails_with(proc, "scaffold_root must be inside workspace root", "scaffold_root_boundary")
    return "scaffold_root traversal blocked"


def test_target_dir_boundary() -> str:
    script = ROOT / "skills" / "skill-creator-pro" / "scripts" / "generate_skill_starter.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        input_path = tmpdir / "input.json"
        output_path = tmpdir / "output.json"
        write_json(
            input_path,
            {
                "skill_name": "secure-test-skill",
                "category": "general",
                "description": "Boundary test skill.",
            },
        )
        proc = run(
            [
                sys.executable,
                str(script),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--format",
                "json",
                "--dry-run",
                "--target-dir",
                "../outside-skill-root",
            ],
            cwd=ROOT,
        )
        assert_fails_with(proc, "target_dir must be inside workspace root", "target_dir_boundary")
    return "target_dir traversal blocked"


def test_allow_outside_workspace_flag() -> str:
    script = ROOT / "skills" / "agentic-mcp-server-builder" / "scripts" / "scaffold_mcp_server.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        input_path = tmpdir / "input.json"
        output_path = tmpdir / "output.json"
        write_json(
            input_path,
            {
                "server_name": "ops-helper",
                "scaffold_root": str(tmpdir / "outside-allowed"),
                "tools": [{"name": "list", "description": "list incidents"}],
            },
        )
        proc = run(
            [
                sys.executable,
                str(script),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--format",
                "json",
                "--dry-run",
                "--allow-outside-workspace",
            ],
            cwd=ROOT,
        )
        if proc.returncode != 0:
            raise SecurityTestError(
                "allow_outside_workspace_flag: expected success with explicit override\n"
                f"stdout={proc.stdout}\nstderr={proc.stderr}"
            )
        if not output_path.exists():
            raise SecurityTestError("allow_outside_workspace_flag: output artifact missing")
    return "outside workspace override works"


def test_oversized_input_rejected() -> str:
    script = ROOT / "skills" / "ml-experiment-tracker" / "scripts" / "build_experiment_plan.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        input_path = tmpdir / "oversized.json"
        output_path = tmpdir / "output.json"
        payload = {"blob": "A" * (MAX_INPUT_BYTES + 256)}
        write_json(input_path, payload)

        proc = run(
            [
                sys.executable,
                str(script),
                "--input",
                str(input_path),
                "--output",
                str(output_path),
                "--format",
                "json",
                "--dry-run",
            ],
            cwd=ROOT,
        )
        assert_fails_with(proc, "Input file exceeds", "oversized_input_rejected")
    return "oversized payload rejected"


def test_packaging_rejects_symlink() -> str:
    script = ROOT / "tools" / "package_skills_for_claude.py"
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        skills_dir = tmpdir / "skills"
        skill_dir = skills_dir / "sample-skill"
        output_dir = tmpdir / "zips"
        skill_dir.mkdir(parents=True, exist_ok=True)

        (skill_dir / "SKILL.md").write_text(
            "---\nname: sample-skill\ndescription: Security packaging test.\n---\n",
            encoding="utf-8",
        )
        (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
        (skill_dir / "agents" / "openai.yaml").write_text(
            "interface:\n"
            "  display_name: \"Sample Skill\"\n"
            "  short_description: \"Sample security packaging validation\"\n"
            "  default_prompt: \"Use $sample-skill for packaging checks.\"\n",
            encoding="utf-8",
        )
        (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
        (skill_dir / "scripts" / "run.py").write_text("print('ok')\n", encoding="utf-8")

        secret_file = tmpdir / "secret.txt"
        secret_file.write_text("sensitive-data\n", encoding="utf-8")
        link_path = skill_dir / "leak.txt"
        try:
            link_path.symlink_to(secret_file)
        except OSError as exc:
            return f"symlink test skipped ({exc.__class__.__name__})"

        proc = run(
            [
                sys.executable,
                str(script),
                "--skills-dir",
                str(skills_dir),
                "--output",
                str(output_dir),
            ],
            cwd=ROOT,
        )
        assert_fails_with(proc, "Packaging aborted", "packaging_rejects_symlink")
    return "packaging rejects symlink/reparse paths"


def main() -> int:
    checks = [
        test_scaffold_root_boundary,
        test_target_dir_boundary,
        test_allow_outside_workspace_flag,
        test_oversized_input_rejected,
        test_packaging_rejects_symlink,
    ]
    results: list[str] = []

    for check in checks:
        results.append(check())

    print(json.dumps({"status": "ok", "checks": results}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SecurityTestError as exc:
        print(f"Security regression test failure: {exc}")
        raise SystemExit(1)
