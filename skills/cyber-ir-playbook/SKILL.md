---
name: cyber-ir-playbook
description: Build incident response timelines and report packs aligned to structured IR phases. Use when security teams need to convert raw incident events into investigation summaries, containment status, recovery actions, and stakeholder-ready reports.
---

# Cyber IR Playbook

## Overview

Convert incident events into a standardized response timeline and phase-based report.

## Workflow

1. Ingest incident events with timestamps.
2. Classify events into detection, containment, eradication, recovery, or post-incident phases.
3. Build ordered timeline and summarize current phase completion.
4. Produce a report artifact for internal and executive audiences.

## Use Bundled Resources

- Run `scripts/ir_timeline_report.py` to generate a deterministic timeline report.
- Read `references/ir-phase-guide.md` for phase mapping guidance.

## Guardrails

- Focus on defensive incident handling and post-incident learning.
- Do not provide offensive exploitation instructions.
