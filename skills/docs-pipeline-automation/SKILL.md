---
name: docs-pipeline-automation
description: Build repeatable data-to-document pipelines for Google Docs outputs using structured source definitions. Use when teams need automated report assembly, periodic status documents, and consistent formatting from Sheets/Drive inputs.
---

# Docs Pipeline Automation

## Overview

Create deterministic pipelines that transform Workspace data sources into generated Docs outputs.

## Workflow

1. Define pipeline name, sources, template, and destination.
2. Normalize source extraction and section mapping steps.
3. Build report assembly sequence and publish target.
4. Export implementation-ready pipeline artifact.

## Use Bundled Resources

- Run `scripts/compose_docs_pipeline.py` for deterministic pipeline output.
- Read `references/docs-pipeline-guide.md` for document assembly guidance.

## Guardrails

- Keep source mapping explicit and versioned.
- Include fallback behavior for missing sections.
