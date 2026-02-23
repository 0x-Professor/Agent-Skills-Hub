@echo off
setlocal

python tests\smoke\validate_all_skills.py
if errorlevel 1 exit /b 1

python tests\smoke\run_smoke.py
if errorlevel 1 exit /b 1

echo [OK] Validation and smoke tests passed.
