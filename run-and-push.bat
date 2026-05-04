@echo off

set BRANCH=main

:: Reset any local changes
git fetch origin
git reset --hard origin/%BRANCH%

:: Pull with rebase instead of merge
git pull --rebase origin %BRANCH%
if %errorlevel% neq 0 (
    echo Conflict detected. Cleaning up...
    git rebase --abort
    exit /b 1
)

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