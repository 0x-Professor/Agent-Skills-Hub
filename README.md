# Agent Skills Hub

[![CI](https://github.com/0x-Professor/Agent-Skills-Hub/actions/workflows/ci.yml/badge.svg)](https://github.com/0x-Professor/Agent-Skills-Hub/actions/workflows/ci.yml)
![GitHub Release](https://img.shields.io/github/v/release/0x-Professor/Agent-Skills-Hub)
![License](https://img.shields.io/github/license/0x-Professor/Agent-Skills-Hub)

Production-ready skill packs for AI coding agents: Codex, Claude Code, Cursor, Aider, Continue, and Agent Skills-compatible runtimes.

This repository focuses on deterministic skill contracts, strong validation, and reusable automation patterns for:
- agentic workflows and MCP servers
- web engineering pipelines
- ML/DL experiment workflows
- cybersecurity triage and authorized penetration-testing workflows

## Why This Repository

- Standardized skill contract (`SKILL.md`, `agents/openai.yaml`, script CLI contract)
- Cross-platform packaging and compatibility checks
- Deterministic dry-run behavior for safe automation
- Scenario tests validating end-to-end skill behavior
- Security-first controls in pentest skills (scope gating and authorization requirements)

## Repository Layout

```text
./
  .github/
    workflows/
  skills/
  tests/
    smoke/
    scenarios/
    security/
  tools/
```

## Skill Packs

This repository ships 44 production-ready skills:
- 1 meta skill: `skill-creator-pro`
- 43 domain skills across cybersecurity, AI/ML+DL, agentic AI, daily automation, web engineering, and authorized pentest operations

### Web Builder Skills

- `web-stack-planner`
- `web-ux-architect`
- `web-frontend-designer`
- `web-backend-builder`
- `web-auth-integrator`
- `web-database-validator`
- `web-api-tester`
- `web-frontend-tester`
- `web-security-auditor`
- `web-deploy-launcher`

### Pentester Skills

- `pentest-engagement-planner`
- `pentest-recon-osint`
- `pentest-network-scanner`
- `pentest-vuln-analyzer`
- `pentest-web-app-attacker`
- `pentest-api-attacker`
- `pentest-auth-bypass`
- `pentest-injection-engine`
- `pentest-network-exploiter`
- `pentest-priv-escalation`
- `pentest-active-directory`
- `pentest-cloud-auditor`
- `pentest-container-k8s`
- `pentest-wireless-attacker`
- `pentest-social-engineer`
- `pentest-mobile-auditor`
- `pentest-lateral-movement`
- `pentest-c2-operator`
- `pentest-data-exfil-tester`
- `pentest-redteam-ops`
- `pentest-report-generator`
- `pentest-remediation-validator`
- `nmap-pentest-scans`

## Skill Contract

Each skill follows:
- `SKILL.md` with YAML frontmatter (`name`, `description`)
- `agents/openai.yaml` with `display_name`, `short_description`, `default_prompt`
- optional `scripts/`, `references/`, `assets/`

All executable scripts follow this CLI contract:
- `--input <path>`
- `--output <path>`
- `--format json|md|csv` (default `json`)
- `--dry-run`

Pentest skill scripts also enforce:
- `--scope <scope.json>`
- `--target <target>`
- `--i-have-authorization` for non-dry-run mode

JSON output contract:
- `status`: `ok|warning|error`
- `summary`
- `artifacts`
- `details`

## Quick Start

Requirements:
- Python 3.10+
- `pyyaml`
- `skills-ref`

Install dependencies:

```bat
python -m pip install --user pyyaml skills-ref
```

Run full checks:

```bat
tools\run_checks.bat
```

Run key checks manually:

```bat
python tests\smoke\validate_all_skills.py
python tests\smoke\validate_web_builder_skills.py
python tests\smoke\validate_pentest_skills.py
python tests\smoke\run_smoke.py
python tests\scenarios\test_web_builder_skills.py
python tests\scenarios\test_pentest_skills.py
python tests\scenarios\run_agentic_scenarios.py
python tests\scenarios\run_agentskills_reference_checks.py
python tests\security\run_security_regressions.py
```

## CI

GitHub Actions validates:
- all skill metadata and contracts
- smoke tests and scenario tests
- security regression checks
- packaging compatibility for Claude uploads

## Releases and Changelog

- See [CHANGELOG.md](CHANGELOG.md) for version history.
- GitHub releases are generated from tags and curated release notes.
- Release configuration lives in `.github/release.yml`.
- Current release notes source: `releases/v3.0.1.md`

## SEO and Discoverability Notes

For repository discoverability in GitHub search, keep:
- concise keyword-rich repository description
- clear README headings and domain terms (AI agents, MCP, pentest skills, web builder skills)
- active releases with tags and release notes
- consistent labels and issue templates

Recommended GitHub repository topics:
- `ai-agents`
- `codex`
- `claude-code`
- `agent-skills`
- `mcp`
- `prompt-engineering`
- `developer-tools`
- `security-automation`
- `penetration-testing`
- `owasp`
- `mitre-attack`
- `devsecops`

## Compatibility

- Codex: https://developers.openai.com/codex/configuration#skills
- Claude custom skills: https://support.anthropic.com/en/articles/12522847-building-custom-skills-for-claude-ai
- Agent Skills spec: https://agentskills.io/spec

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security Scope

Cybersecurity and pentest skills are for authorized use only.  
Unauthorized access testing is illegal. Use dry-run mode unless written authorization exists.
