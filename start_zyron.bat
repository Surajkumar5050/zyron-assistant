@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

:: --- ANSI COLOR DEFS ---
for /f "delims=" %%a in ('powershell -NoProfile -Command "[char]27"') do set "ESC=%%a"
set "C_RST=%ESC%[0m"
set "C_CYN=%ESC%[36m"
set "C_BCYN=%ESC%[96m"
set "C_MAG=%ESC%[35m"
set "C_BMAG=%ESC%[95m"
set "C_GRN=%ESC%[32m"
set "C_RED=%ESC%[31m"
set "C_GRAY=%ESC%[90m"

title ⚡ ZYRON AGENT - ACTIVE ⚡

cls
echo %C_MAG%
echo    .──────────────────────────────────────.
echo    │   %C_BCYN%⚡ ZYRON SYSTEM INITIALIZATION ⚡%C_MAG%   │
echo    '──────────────────────────────────────'%C_RST%
echo.

:: Check if venv exists
echo   %C_CYN%[1/2]%C_RST% Verifying Environment...
if not exist venv (
    echo.
    echo   %C_RED%[X] Virtual environment not found.%C_RST%
    echo   %C_GRAY%Please run 'setup.bat' first to configure the system.%C_RST%
    echo.
    pause
    exit /b 1
)
echo   %C_GRN%[✓] Environment Verified.%C_RST%
echo.

:: Activate and Run
echo   %C_CYN%[2/2]%C_RST% Launching Zyron Core...
call venv\Scripts\activate

echo.
echo   %C_GRN%┌──────────────────────────────────────┐
echo   │      🤖  ZYRON IS NOW ACTIVE         │
echo   │   %C_GRAY%Press Ctrl+C to safely exit%C_GRN%      │
echo   └──────────────────────────────────────┘%C_RST%
echo.

python -m zyron.agents.telegram
echo.
echo   %C_GRAY%Zyron process has terminated.%C_RST%
pause