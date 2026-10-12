@echo off
REM Energy Provider Checker - Launch with latest data
REM Just double-click this file to run the app with fresh data!

echo.
echo ============================================================
echo  ^⚡ Auckland Energy Provider Checker
echo ============================================================
echo.
echo  🔄 Refreshing with latest data...
echo.

python launch_app.py

if errorlevel 1 (
    echo.
    echo ❌ Error: Make sure Python is installed and in your PATH
    echo.
    echo Try this instead:
    echo   1. Open Command Prompt here
    echo   2. Run: python launch_app.py
    pause
)
