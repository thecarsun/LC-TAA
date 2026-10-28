@echo off
REM ============================================================
REM LC-TAA Automated Data Pipeline - v8.1
REM Updated: 2026-10-28
REM
REM Purpose:
REM Runs the local Python scraper and synchronizes updated
REM litigation data with GitHub for the Streamlit dashboard.
REM
REM v8.1 Reliability Improvements:
REM - Validate scraper execution before running Git commands.
REM - Check Git staging, commit, and push exit codes.
REM - Skip unnecessary commits when no data changes exist.
REM - Log execution failures and return nonzero exit codes
REM   so Windows Task Scheduler can detect failed runs.
REM ============================================================

setlocal


setlocal

set "PROJECT=C:\Users\Car\grepos\LC-TAA"
set "LOG=%PROJECT%\update_log.txt"
set "PYTHON=C:\Users\Car\AppData\Local\Python\pythoncore-3.14-64\python.exe"

cd /d "%PROJECT%"
if errorlevel 1 exit /b 1

echo ======================================== >> "%LOG%"
echo Starting LC-TAA v8.1 data update >> "%LOG%"
echo %date% %time% >> "%LOG%"

echo Running scraper... >> "%LOG%"
"%PYTHON%" "%PROJECT%\src\scrape_tracker.py" >> "%LOG%" 2>&1

if errorlevel 1 (
    echo ERROR: Scraper failed. Git update cancelled. >> "%LOG%"
    exit /b 1
)

echo Scraper completed successfully. >> "%LOG%"

echo Staging updated data... >> "%LOG%"
git add data/processed/cases.csv data/processed/filters.json data/processed/last_run.txt >> "%LOG%" 2>&1

if errorlevel 1 (
    echo ERROR: Git staging failed. >> "%LOG%"
    exit /b 1
)

git diff --cached --quiet
if errorlevel 2 (
    echo ERROR: Git change detection failed. >> "%LOG%"
    exit /b 1
)
if not errorlevel 1 (
    echo No data changes detected. >> "%LOG%"
) else (
    echo Committing updated data... >> "%LOG%"
    git commit -m "Automated data update %date%" >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo ERROR: Git commit failed. >> "%LOG%"
        exit /b 1
    )
)

echo Synchronizing with GitHub... >> "%LOG%"
git push >> "%LOG%" 2>&1
if errorlevel 1 (
    echo ERROR: Git push failed. >> "%LOG%"
    exit /b 1
)

echo SUCCESS: LC-TAA update completed. >> "%LOG%"
echo %date% %time% >> "%LOG%"
exit /b 0
