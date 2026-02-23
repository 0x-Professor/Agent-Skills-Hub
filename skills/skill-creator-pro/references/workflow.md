# Skill Creation Workflow

## Purpose

Use this workflow to keep skill quality consistent and predictable across the repository.

## Steps

1. Define trigger intent in one sentence.
2. Write 2-3 concrete user prompts that must trigger the skill.
3. Decide what should live in:
   - `SKILL.md` (core operating procedure)
   - `references/` (long-form context)
   - `scripts/` (deterministic actions)
   - `assets/` (output templates and static files)
4. Add `agents/openai.yaml` with:
   - `display_name`
   - `short_description` (25-64 chars)
   - `default_prompt` mentioning `$skill-name`
5. Enforce script contract for every executable file:
   - `--input`
   - `--output`
   - `--format json|md|csv`
   - `--dry-run`
6. Validate and smoke-test before publishing.

## Review Checklist

- Frontmatter contains only required keys.
- Description clearly states when to use the skill.
- References are targeted and not repetitive.
- Scripts are deterministic and safe under `--dry-run`.
- Security guidance avoids unsafe offensive content unless explicitly bounded.
