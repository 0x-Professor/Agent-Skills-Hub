# Agent Skills Hub

Public skill pack for AI coding/automation agents.

This repository ships 11 production-ready skills:
- 1 meta skill: `skill-creator-pro`
- 10 domain skills across cybersecurity, AI/ML+DL, agentic AI, and daily automation

## Repo Layout

```text
./
  .github/workflows/ci.yml
  skills/
  tests/smoke/
  tests/scenarios/
  tools/
```

## Included Skills

- `skill-creator-pro`
- `cyber-kev-triage`
- `cyber-ir-playbook`
- `cyber-owasp-review`
- `ml-experiment-tracker`
- `ml-model-eval-benchmark`
- `dl-transformer-finetune`
- `agentic-mcp-server-builder`
- `agentic-workflow-automation`
- `google-workspace-automation`
- `docs-pipeline-automation`

## Skill Contract

Each skill follows:
- `SKILL.md` with YAML frontmatter (`name`, `description`)
- `agents/openai.yaml` with `display_name`, `short_description`, `default_prompt`
- Optional `scripts/`, `references/`, `assets/`

All executable scripts follow the same CLI contract:
- `--input <path>`
- `--output <path>`
- `--format json|md|csv` (default `json`)
- `--dry-run`

Output contract for `json` format:
- `status`: `ok|warning|error`
- `summary`: short result
- `artifacts`: output artifacts
- `details`: tool-specific object

## Validate Locally

Requirements:
- Python 3.10+
- `pyyaml`
- `skills-ref`

```bat
python -m pip install --user pyyaml skills-ref
python tests\smoke\validate_all_skills.py
python tests\smoke\run_smoke.py
python tests\scenarios\run_agentic_scenarios.py
python tests\scenarios\run_agentskills_reference_checks.py
tools\run_checks.bat
```

## CI

GitHub Actions runs:
- skill validation
- smoke tests for every script (`--help`, `json`, `md`, and `csv` dry-runs)
- scenario/E2E tests for agentic application flows
- `skills-ref` compatibility checks against Agent Skills reference APIs

## Cross-Platform Compatibility

This repository follows the Agent Skills pattern:
- `SKILL.md` for core behavior and triggers
- `agents/openai.yaml` for OpenAI/Codex UI metadata
- deterministic scripts with `--dry-run`

Compatibility notes:
- Codex:
  - Skills can live in repo-level `.agents/skills` or user-level configured skill paths.
  - This repo keeps source-of-truth skills in `skills/`.
  - Copy a skill folder into your Codex skill path, or install from this repository.
  - Reference: https://developers.openai.com/codex/configuration#skills
- Claude Code / Claude.ai custom skills:
  - Zip each skill with `<skill-name>/SKILL.md` at zip root for upload.
  - Keep `description` <= 200 chars for Claude.ai upload compatibility.
  - Reference: https://support.anthropic.com/en/articles/12522847-building-custom-skills-for-claude-ai
- Agent Skills ecosystem:
  - Reference spec and integrations: https://agentskills.io/spec and https://agentskills.io/integrations

## Agent Skills Compliance

This repository is aligned to the Agent Skills reference model from `agentskills.io`:
- every skill includes `SKILL.md` with required frontmatter (`name`, `description`)
- frontmatter `name` matches the skill folder name
- optional frontmatter keys accepted by validation include `compatibility`, `license`, `allowed-tools`, and `metadata`
- every skill includes `agents/openai.yaml` with `display_name`, `short_description`, and `default_prompt`
- compatibility checks are validated in `tests/scenarios/run_agentskills_reference_checks.py` using `skills-ref`

## Packaging for Claude Uploads

Use this helper to package all skills as individual zip files:

```bat
python tools\package_skills_for_claude.py --output artifacts\claude-zips
```

## Production Readiness Checks

The automated checks enforce:
- valid frontmatter and metadata contracts
- cross-platform description limits (Claude-compatible)
- script CLI contract across all skills
- deterministic dry-run behavior for every script
- scenario-level integration coverage across all 11 skills
- Agent Skills reference library validation and prompt generation checks

## Contributing

See `CONTRIBUTING.md` for contribution workflow, quality gates, and review requirements.

## Publish To GitHub

Prerequisites:
- Git CLI installed
- GitHub CLI (`gh`) installed and authenticated

```bat
gh auth login
git init -b main
git add .
git commit -m "feat: initial public release of agent skills hub v1"
gh repo create agent-skills-hub --public --source . --remote origin --push
git tag v1.0.0
git push origin v1.0.0
```

Or run:

```bat
tools\publish_github.bat
```

## Security Scope

Cybersecurity skills in this repo are defensive or tooling-oriented. They do not ship exploit payloads or real-target offensive playbooks.
