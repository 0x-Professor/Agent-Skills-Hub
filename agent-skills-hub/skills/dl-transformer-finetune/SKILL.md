---
name: dl-transformer-finetune
description: Build transformer fine-tuning run plans with task-specific settings, hyperparameters, and model card outputs. Use when teams need repeatable DL fine-tuning configuration for Hugging Face/PyTorch style workflows.
---

# DL Transformer Finetune

## Overview

Generate reproducible fine-tuning run plans for transformer models and downstream tasks.

## Workflow

1. Define base model, task type, and dataset.
2. Set training hyperparameters and evaluation cadence.
3. Produce run plan plus model card skeleton.
4. Export configuration-ready artifacts for training pipelines.

## Use Bundled Resources

- Run `scripts/build_finetune_plan.py` for deterministic plan output.
- Read `references/finetune-guide.md` for hyperparameter baseline guidance.

## Guardrails

- Keep run plans reproducible with explicit seeds and output directories.
- Include evaluation and rollback criteria.
