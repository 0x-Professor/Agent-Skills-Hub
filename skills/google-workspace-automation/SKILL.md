---
name: google-workspace-automation
description: Design Google Workspace automations across Gmail, Drive, Sheets, and Calendar with scope-aware plans and audit-ready outputs. Use when creating repeatable daily task automation that requires explicit API scope and action sequencing.
---

# Google Workspace Automation

## Overview

Create structured automation plans for common Gmail, Drive, Sheets, and Calendar workflows.

## Workflow

1. Define automation goal, services, and actions.
2. Derive required OAuth scopes and integration boundaries.
3. Build execution plan with schedule and retry behavior.
4. Export auditable artifact for implementation.

## Use Bundled Resources

- Run `scripts/plan_workspace_automation.py` for deterministic automation planning.
- Read `references/workspace-guide.md` for scope and quota considerations.

## Guardrails

- Always declare least-privilege scopes.
- Keep automations idempotent and auditable.
