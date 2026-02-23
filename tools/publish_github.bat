@echo off
setlocal

git --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] git is not installed or not on PATH.
  exit /b 1
)

gh --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] gh is not installed or not on PATH.
  exit /b 1
)

gh auth status >nul 2>&1
if errorlevel 1 (
  echo [ERROR] GitHub CLI is not authenticated. Run: gh auth login
  exit /b 1
)

git init -b main
git add .
git commit -m "feat: initial public release of agent skills hub v1"
gh repo create agent-skills-hub --public --source . --remote origin --push
git tag v1.0.0
git push origin v1.0.0

echo [OK] Published repository and pushed tag v1.0.0
