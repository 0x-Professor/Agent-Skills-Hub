# Contributing

## Scope

Contribute improvements to:
- existing skills in `skills/`
- test coverage in `tests/`
- tooling in `tools/`
- CI quality gates in `.github/workflows/`

Keep changes aligned with Agent Skills conventions from:
- https://agentskills.io/home
- https://agentskills.io/spec

## Prerequisites

- Python 3.10+
- Git
- `pyyaml`
- `skills-ref`

Install dependencies:

```bat
python -m pip install --user pyyaml skills-ref
```

## Skill Authoring Rules

Each skill must include:
- `SKILL.md`
- `agents/openai.yaml`

`SKILL.md` frontmatter:
- required: `name`, `description`
- optional: `compatibility`, `license`, `allowed-tools`, `metadata`
- `name` must equal the skill folder name
- `description` must be explicit and non-empty

Executable scripts should support:
- `--input`
- `--output`
- `--format json|md|csv`
- `--dry-run`

JSON output contract:
- `status`
- `summary`
- `artifacts`
- `details`

## Testing Requirements

Run all checks before opening a PR:

```bat
tools\run_checks.bat
```

Equivalent manual commands:

```bat
python tests\smoke\validate_all_skills.py
python tests\smoke\run_smoke.py
python tests\scenarios\run_agentic_scenarios.py
python tests\scenarios\run_agentskills_reference_checks.py
python tools\package_skills_for_claude.py --output artifacts\claude-zips
```

## Pull Request Guidance

- Keep PRs focused and reviewable.
- Include tests with any behavior change.
- Update references and docs when contracts change.
- For cybersecurity skills, keep guidance defensive/tooling-oriented and avoid exploit payload content.

## Release Guidance

After merge, verify CI is green and publish from `main`.
