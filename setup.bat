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

:: ================= PYTHON CHECK =================
echo.
echo   !C_CYN![1/6]!C_RST! Scanning for Python...

set "PYTHON_CMD="
set "PYTHON_VER="

for %%V in (3.11 3.10 3.12) do (
    if not defined PYTHON_CMD (
        py -%%V --version >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=py"
            set "PYTHON_VER=-%%V"
            echo     !C_GRN![OK]!C_RST! Python %%V found (Launcher)
        )
    )
)

if not defined PYTHON_CMD (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
        set "PYTHON_VER="
        echo     !C_GRN![OK]!C_RST! Python found (Default PATH)
    )
)

if not defined PYTHON_CMD (
    echo.
    echo     !C_RED![ERROR]!C_RST! Python 3.10+ not found.
    pause
    exit /b 1
)

echo.

:: ================= ENVIRONMENT =================
echo   !C_CYN![2/6]!C_RST! Creating virtual environment...

if exist venv (
    :: Kill any python processes that may be locking venv files
    taskkill /f /im python.exe >nul 2>&1
    taskkill /f /im pythonw.exe >nul 2>&1
    :: Retry deletion up to 3 times with a pause
    for /l %%i in (1,1,3) do (
        if exist venv (
            rmdir /s /q venv >nul 2>&1
            timeout /t 1 /nobreak >nul
        )
    )
)

%PYTHON_CMD% %PYTHON_VER% -m venv venv
if errorlevel 1 (
    :: One more attempt after a longer wait (antivirus may have briefly locked)
    echo     !C_YLW![WARN]!C_RST! Retrying venv creation...
    timeout /t 3 /nobreak >nul
    %PYTHON_CMD% %PYTHON_VER% -m venv venv
)
if errorlevel 1 (
    echo     !C_RED![ERROR]!C_RST! Failed to create venv. Try running setup.bat as Administrator.
    pause
    exit /b 1
)

echo     !C_GRN![OK]!C_RST! venv created.
echo.

:: ================= DEPENDENCIES =================
echo   !C_CYN![3/6]!C_RST! Installing dependencies...

call venv\Scripts\activate.bat
venv\Scripts\python.exe -m pip install --upgrade pip >nul
venv\Scripts\python.exe -m pip install -e .

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
echo   !C_GRN!Setup complete.!C_RST!
echo.
pause
exit /b
