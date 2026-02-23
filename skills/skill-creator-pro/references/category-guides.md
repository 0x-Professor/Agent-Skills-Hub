# Category Guides

## Cybersecurity

- Keep guidance defensive or tooling-oriented by default.
- Map findings to known frameworks (KEV, NIST IR, OWASP).
- Avoid exploit payloads and real-target operational instructions.
- Prioritize actionable triage, mitigation, and reporting.

## AI/ML + Deep Learning

- Emphasize experiment reproducibility.
- Require explicit metrics and acceptance thresholds.
- Include run metadata, versioning, and model card outputs.
- Keep training plans configurable through input files.

## Agentic AI and MCP

- Define tool boundaries and input/output schemas.
- Add fallback behavior when upstream services fail.
- Keep generated workflow JSON deterministic and valid.
- Include lightweight contract checks for generated artifacts.

## Google Workspace and Daily Automation

- Declare OAuth scopes explicitly.
- Include quota and retry behavior.
- Keep outputs auditable (logs, summaries, artifacts).
- Prioritize idempotent automations for repeated runs.
