# Changelog

All notable changes to this project are documented in this file.

The format follows Keep a Changelog principles and uses Semantic Versioning.

## [Unreleased]

### Added
- Added `nmap-pentest-scans` skill with scope-validated Nmap planning workflow, command templates, and deterministic output artifacts.

## [v3.0.2] - 2026-02-26

### Changed
- Hardened shared pentest runtime scope validation:
  - handles invalid `scope.json` gracefully
  - supports broader target matching (domain/url/ip-range/aws-account/apk variants)
  - applies out-of-scope checks to host-normalized targets
- Hardened input handling for malformed JSON payloads in pentest scripts.

### Added
- Extended pentest scenario coverage for all 22 skills:
  - multiple scope target-type scenarios
  - missing and invalid scope file behavior
  - non-dry-run authorization gating checks
  - live-mode artifact creation checks

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
