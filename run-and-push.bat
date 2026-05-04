@echo off

set BRANCH=main

:: Pull from a specific branch (e.g., test-branch)
git pull origin %BRANCH%

:: Run your Python script
python occupancy.py

:: Check for changes
git status --porcelain | findstr . >nul
if %errorlevel% == 1 exit /b

:: Set custom Git identity
git config user.name "Local Actions Bot"
git config user.email "actions@local.com"

:: Push to the same branch
git add .
git commit -m "Update pool occupancy data"
git push origin %BRANCH%