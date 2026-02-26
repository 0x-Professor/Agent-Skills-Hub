## Summary

- What changed
- Why it changed
- Impacted areas

## Validation

- [ ] `python tests/smoke/validate_all_skills.py`
- [ ] `python tests/smoke/run_smoke.py`
- [ ] `python tests/scenarios/run_agentic_scenarios.py`
- [ ] `python tests/scenarios/run_agentskills_reference_checks.py`
- [ ] `python tests/security/run_security_regressions.py`

If pentest skills changed:
- [ ] `python tests/smoke/validate_pentest_skills.py`
- [ ] `python tests/scenarios/test_pentest_skills.py`

## Skill Contract Checklist

- [ ] `SKILL.md` frontmatter valid and `name` matches folder
- [ ] `agents/openai.yaml` has required interface keys
- [ ] scripts honor `--dry-run` and output contract
- [ ] docs/references updated

## Release Notes

- [ ] Add or update `CHANGELOG.md` entry if user-facing behavior changed
