# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog principles and uses Semantic Versioning.

## [v3.0.1] - 2026-02-26

### Added
- Dedicated pentester skills section in `README.md` for better pack discoverability.
- GitHub issue templates for bug reports, feature requests, and skill proposals.
- Pull request template for consistent contribution quality.
- Release configuration file `.github/release.yml` for structured GitHub releases.

### Changed
- Expanded `CONTRIBUTING.md` with maintainer-grade contribution and release guidance.
- Refined repository README for discoverability and onboarding quality.
- Expanded `skills/autonomous-pentester/references/master-tools.md` into a full framework/tool table.

## [v3.0.0] - 2026-02-26

### Added
- Autonomous pentester skill pack with 22 skills (`skills/pentest-*`).
- Shared pentest contracts and helpers:
  - `skills/autonomous-pentester/shared/scope_schema.json`
  - `skills/autonomous-pentester/shared/finding_schema.json`
  - `skills/autonomous-pentester/shared/pentest_common.py`
- Pentest smoke/scenario checks:
  - `tests/smoke/validate_pentest_skills.py`
  - `tests/scenarios/test_pentest_skills.py`
- CI and local check integration for pentest validations.

## [v2.0.0] - 2026-02-25

### Added
- Web builder skill pack and full pipeline validation.

