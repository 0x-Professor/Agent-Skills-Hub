# Contributing

Thanks for improving Agent Skills Hub.

## Project Goals

This repository prioritizes:
- deterministic, testable skills
- clear metadata contracts
- cross-platform compatibility
- safe defaults for security-related automation

## Prerequisites

- Python 3.10+
- Git
- GitHub CLI (`gh`) for release and PR workflows (recommended)
- `pyyaml`
- `skills-ref`

Install dependencies:

```bat
python -m pip install --user pyyaml skills-ref
```

## Branch and Commit Conventions

- Branch naming:
  - `feat/<topic>`
  - `fix/<topic>`
  - `docs/<topic>`
  - `chore/<topic>`
- Commit style (recommended):
  - `feat: ...`
  - `fix: ...`
  - `docs: ...`
  - `chore: ...`

## Skill Authoring Contract

Each skill must include:
- `SKILL.md`
- `agents/openai.yaml`
- at least one script in `scripts/*.py`

`SKILL.md` frontmatter:
- required: `name`, `description`
- optional: `compatibility`, `license`, `allowed-tools`, `metadata`
- `name` must match folder name
- `description` must be explicit and non-empty

Executable script contract:
- `--input`
- `--output`
- `--format json|md|csv`
- `--dry-run`

JSON output contract:
- `status`
- `summary`
- `artifacts`
- `details`

Pentest skill requirements:
- enforce scope validation before any active action
- refuse non-dry-run execution without explicit authorization confirmation
- keep outputs in canonical finding schema

## Testing Requirements

Run before opening a PR:

```bat
tools\run_checks.bat
```

Minimum manual checks:

```bat
python tests\smoke\validate_all_skills.py
python tests\smoke\run_smoke.py
python tests\scenarios\run_agentic_scenarios.py
python tests\scenarios\run_agentskills_reference_checks.py
python tests\security\run_security_regressions.py
```

For pentest changes also run:

```bat
python tests\smoke\validate_pentest_skills.py
python tests\scenarios\test_pentest_skills.py
```

## Documentation Requirements

Update docs whenever contracts or behavior change:
- `README.md`
- skill-level `references/`
- `CHANGELOG.md`

## Pull Request Checklist

- [ ] focused scope and clear title
- [ ] tests added/updated for behavior changes
- [ ] all required checks pass locally
- [ ] docs updated
- [ ] no unrelated file churn

## Release Process (Maintainers)

1. Merge approved PRs to `main`.
2. Run `tools\run_checks.bat`.
3. Update `CHANGELOG.md`.
4. Tag release (`vX.Y.Z`) and push tags.
5. Publish GitHub release with curated notes.

## Security and Legal

Cybersecurity content in this repository is intended for authorized defensive use only.  
Do not submit unauthorized exploitation payloads or instructions targeting real systems without legal scope controls.
