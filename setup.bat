@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: Force UTF-8 (silently)
chcp 65001 >nul 2>&1

:: ================= COLOR INITIALIZATION =================
for /f %%a in ('echo prompt $E^|cmd') do set "ESC=%%a"

set "C_RST=%ESC%[0m"
set "C_CYN=%ESC%[36m"
set "C_BCYN=%ESC%[96m"
set "C_MAG=%ESC%[35m"
set "C_BMAG=%ESC%[95m"
set "C_GRN=%ESC%[32m"
set "C_RED=%ESC%[31m"
set "C_YLW=%ESC%[33m"

cd /d "%~dp0"
title ZYRON ASSISTANT - PREMIUM SETUP

cls

:: ================= BANNER =================
echo.
echo   !C_BCYN!===========================================================!C_RST!
echo   !C_BCYN!                                                           !C_RST!
echo   !C_BMAG!      ______  _     _  ____    ___   _   _               !C_RST!
echo   !C_BMAG!     ^|_  /\ \^| ^|   ^| ^|  _ \  / _ \ ^| \ ^| ^|              !C_RST!
echo   !C_BMAG!       / /  \ V /  ^| ^|_) ^|^| ^| ^| ^|^|  \^| ^|              !C_RST!
echo   !C_BMAG!      /___   \_/   ^|____/  \___/ ^|_^|\__^|              !C_RST!
echo   !C_BCYN!                                                           !C_RST!
echo   !C_CYN!           ZYRON ASSISTANT  --  Setup Wizard               !C_RST!
echo   !C_BCYN!                                                           !C_RST!
echo   !C_BCYN!===========================================================!C_RST!
echo.
echo   !C_YLW!  Welcome! Setting up your ZYRON environment...!C_RST!
echo   !C_YLW!  Please wait while we configure everything for you.!C_RST!
echo.
echo   !C_BCYN!-----------------------------------------------------------!C_RST!
echo.

:: ================= PYTHON CHECK =================
echo   !C_CYN![1/6]!C_RST! Scanning for Python...

set "PYTHON_CMD="

for %%V in (3.11 3.10 3.12) do (
    py -%%V --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py -%%V"
        echo     !C_GRN![OK]!C_RST! Python %%V found (Launcher)
        goto :FoundPython
    )
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    echo     !C_GRN![OK]!C_RST! Python found (Default PATH)
    goto :FoundPython
)

echo.
echo     !C_RED![ERROR]!C_RST! Python 3.10+ not found.
pause
exit /b 1

:FoundPython
echo.

:: ================= ENVIRONMENT =================
echo   !C_CYN![2/6]!C_RST! Creating virtual environment...

if exist venv (
    rmdir /s /q venv >nul 2>&1
)

%PYTHON_CMD% -m venv venv
if errorlevel 1 (
    echo     !C_RED![ERROR]!C_RST! Failed to create venv.
    pause
    exit /b 1
)

echo     !C_GRN![OK]!C_RST! venv created.
echo.

:: ================= DEPENDENCIES =================
echo   !C_CYN![3/6]!C_RST! Installing dependencies...

call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -e .

if errorlevel 1 (
    echo     !C_RED![ERROR]!C_RST! Dependency installation failed.
    pause
    exit /b 1
)

echo     !C_GRN![OK]!C_RST! Dependencies installed.
echo.

:: ================= OLLAMA CHECK =================
echo   !C_CYN![4/6]!C_RST! Checking Ollama...

ollama --version >nul 2>&1
if errorlevel 1 (
    echo     !C_YLW![WARNING]!C_RST! Ollama not found.
) else (
    echo     !C_GRN![OK]!C_RST! Ollama detected.
)
echo.

:: ================= .ENV FILE =================
echo   !C_CYN![5/6]!C_RST! Checking .env...

if not exist .env (
    (
        echo TELEGRAM_TOKEN=PASTE_TOKEN_HERE
        echo MODEL_NAME=qwen2.5-coder:7b
    )>.env
    echo     !C_YLW![INFO]!C_RST! .env created.
)

echo     !C_GRN![OK]!C_RST! Configuration ready.
echo.

:: ================= STARTUP SHORTCUT =================
echo   !C_CYN![6/6]!C_RST! Startup configuration...

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

choice /c YN /m "Enable Autostart?"
if errorlevel 2 goto :Finish

(
echo Set WshShell = CreateObject("WScript.Shell")
echo Set oShellLink = WshShell.CreateShortcut("%STARTUP_FOLDER%\ZyronAssistant.lnk")
echo oShellLink.TargetPath = "%~dp0run_silent.vbs"
echo oShellLink.WorkingDirectory = "%~dp0"
echo oShellLink.Save
)>create_shortcut.vbs

cscript //nologo create_shortcut.vbs
del create_shortcut.vbs

echo     !C_GRN![OK]!C_RST! Shortcut created.

:Finish
echo.
echo   !C_BCYN!===========================================================!C_RST!
echo   !C_BCYN!                                                           !C_RST!
echo   !C_GRN!           ZYRON ASSISTANT is ready to use!                !C_RST!
echo   !C_BCYN!                                                           !C_RST!
echo   !C_CYN!    All steps completed. Enjoy ZYRON Assistant!            !C_RST!
echo   !C_BCYN!                                                           !C_RST!
echo   !C_BCYN!===========================================================!C_RST!
echo.
pause
exit /b
