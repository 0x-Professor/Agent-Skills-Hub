@echo off
setlocal

python -m pip install --disable-pip-version-check --quiet skills-ref
if errorlevel 1 exit /b 1

python tests\smoke\validate_all_skills.py
if errorlevel 1 exit /b 1

python tests\smoke\validate_web_builder_skills.py
if errorlevel 1 exit /b 1

python tests\smoke\validate_pentest_skills.py
if errorlevel 1 exit /b 1

python tests\smoke\run_smoke.py
if errorlevel 1 exit /b 1

python tests\scenarios\test_web_builder_skills.py
if errorlevel 1 exit /b 1

python tests\scenarios\test_pentest_skills.py
if errorlevel 1 exit /b 1

python tests\scenarios\test_pentest_bug_bounty_programs.py
if errorlevel 1 exit /b 1

python tests\scenarios\test_nmap_pentest_scans_regression.py
if errorlevel 1 exit /b 1

python tests\scenarios\run_agentic_scenarios.py
if errorlevel 1 exit /b 1

python tests\scenarios\run_agentskills_reference_checks.py
if errorlevel 1 exit /b 1

python tests\security\run_security_regressions.py
if errorlevel 1 exit /b 1

python tools\package_skills_for_claude.py --output artifacts\claude-zips
if errorlevel 1 exit /b 1

echo [OK] Validation, smoke tests, scenario tests, and reference checks passed.
