# Agent Skills Hub

Public skill pack for AI coding/automation agents.

This repository ships 11 production-ready skills:
- 1 meta skill: `skill-creator-pro`
- 10 domain skills across cybersecurity, AI/ML+DL, agentic AI, and daily automation

## Repo Layout

```text
agent-skills-hub/
  skills/
  tests/smoke/
  tools/
  .github/workflows/ci.yml
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

```bat
python -m pip install --user pyyaml
python tests\smoke\validate_all_skills.py
python tests\smoke\run_smoke.py
```

## CI

GitHub Actions runs:
- skill validation
- smoke tests for every script (`--help` and `--dry-run`)

## Install Skills In Agent Environments

This repo uses Agent Skills-compatible structure (`SKILL.md` + `agents/openai.yaml`).
Copy any skill folder from `skills/<skill-name>` into your target agent's skills directory.
Use platform docs for exact install path:
- https://agentskills.io/integrations
- https://docs.anthropic.com/en/docs/claude-code/skills

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

## Security Scope

Cybersecurity skills in this repo are defensive or tooling-oriented. They do not ship exploit payloads or real-target offensive playbooks.
