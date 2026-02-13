@echo off
setlocal EnableDelayedExpansion

:: Set encoding to UTF-8
chcp 65001 >nul 2>&1

:: --- PREMIUM COLOR INITIALIZATION ---
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "C_RST=%ESC%[0m"
set "C_CYN=%ESC%[36m"
set "C_BCYN=%ESC%[96m"
set "C_MAG=%ESC%[35m"
set "C_BMAG=%ESC%[95m"
set "C_GRN=%ESC%[32m"
set "C_RED=%ESC%[31m"
set "C_YLW=%ESC%[33m"
set "C_GRAY=%ESC%[90m"

cd /d "%~dp0"
title ⚡ ZYRON ASSISTANT — PREMIUM SETUP ⚡

cls
:: Render Big Zyron Logo using single-line stable PowerShell call
powershell -NoProfile -Command "Write-Host ' '; Write-Host '   .──────────────────────────────────────────────────────────.' -ForegroundColor Magenta; Write-Host '   │                                                          │' -ForegroundColor Magenta; Write-Host '   │   ███████╗██╗   ██╗██████╗  ██████╗ ███╗   ██╗           │' -ForegroundColor Magenta; Write-Host '   │   ╚══███╔╝╚██╗ ██╔╝██╔══██╗██╔═══██╗████╗  ██║           │' -ForegroundColor Magenta; Write-Host '   │     ███╔╝  ╚████╔╝ ██████╔╝██║   ██║██╔██╗ ██║           │' -ForegroundColor Magenta; Write-Host '   │    ███╔╝    ╚██╔╝  ██╔══██╗██║   ██║██║╚██╗██║           │' -ForegroundColor Magenta; Write-Host '   │   ███████╗   ██║   ██║  ██║╚██████╔╝██║ ╚████║           │' -ForegroundColor Magenta; Write-Host '   │   ╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝           │' -ForegroundColor Magenta; Write-Host '   │                                                          │' -ForegroundColor Magenta; Write-Host '   │            ⚡ Z Y R O N   A S S I S T A N T ⚡             │' -ForegroundColor Cyan; Write-Host '   │                                                          │' -ForegroundColor Magenta; Write-Host '   .──────────────────────────────────────────────────────────.' -ForegroundColor Magenta"


echo.
echo   !C_CYN!  ══════════════════════════════════════════════════
echo            !C_BCYN!⚡ SYSTEM INITIALIZATION ENGAGED ⚡!C_CYN!
echo     ══════════════════════════════════════════════════!C_RST!
echo.

:: ===================== STEP 1 - PYTHON CHECK =====================
echo   !C_CYN![1/6]!C_RST! Scanning for Python Environment...

:: First, try python command directly
python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2 delims= " %%v in ('python --version 2^>nul') do set CUR_VER=%%v
    if "!CUR_VER:~0,4!"=="3.11" (
        set "PYTHON_CMD=python"
        echo     !C_GRN![✓] Found Python 3.11!C_RST!
        goto :FoundPython
    )
    if "!CUR_VER:~0,4!"=="3.10" (
        set "PYTHON_CMD=python"
        echo     !C_GRN![✓] Found Python 3.10 ^(Compatible^)!C_RST!
        goto :FoundPython
    )
    if "!CUR_VER:~0,4!"=="3.12" (
        set "PYTHON_CMD=python"
        echo     !C_GRN![✓] Found Python 3.12 ^(Compatible^)!C_RST!
        goto :FoundPython
    )
)

:: Try py launcher as fallback
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.11"
    echo     !C_GRN![✓] Found Python 3.11 ^(via Launcher^)!C_RST!
    goto :FoundPython
)

py -3.10 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.10"
    echo     !C_GRN![✓] Found Python 3.10 ^(via Launcher^)!C_RST!
    goto :FoundPython
)

py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.12"
    echo     !C_GRN![✓] Found Python 3.12 ^(via Launcher^)!C_RST!
    goto :FoundPython
)

echo.
echo     !C_RED![X] CRITICAL: Python 3.10+ not found!!C_RST!
echo     !C_YLW!Please install Python from python.org!C_RST!
echo.
pause
exit /b 1

:FoundPython
echo.

:: ===================== STEP 2 - ENVIRONMENT SETUP =====================
echo   !C_CYN![2/6]!C_RST! Configuring Workspace...

if exist venv (
    echo     !C_YLW![i] Closing active processes...!C_RST!
    taskkill /f /im python.exe /t >nul 2>&1
    taskkill /f /im pythonw.exe /t >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo     !C_YLW![i] Refreshing old files...!C_RST!
    rmdir /s /q venv >nul 2>&1
    if exist venv (
        echo.
        echo     !C_RED![!] ERROR: Access Denied to 'venv' folder.!C_RST!
        echo     !C_YLW!Please close VS Code or any other terminal using this folder.!C_RST!
        echo.
        pause
        exit /b 1
    )
)

echo     !C_CYN![+] Building virtual environment...!C_RST!
%PYTHON_CMD% -m venv venv

if errorlevel 1 (
    echo.
    echo     !C_RED![X] Workspace creation FAILED!!C_RST!
    echo.
    pause
    exit /b 1
)
echo     !C_GRN![✓] Workspace ready.!C_RST!
echo.

:: ===================== STEP 3 - DEPENDENCIES =====================
echo   !C_CYN![3/6]!C_RST! Deploying Neural Modules...
call venv\Scripts\activate
python -m pip install --upgrade pip --quiet
pip install -e .

if errorlevel 1 (
    echo.
    echo     !C_RED![X] Submodule installation FAILED!!C_RST!
    echo.
    pause
    exit /b 1
)
echo     !C_GRN![✓] Systems online.!C_RST!
echo.

:: ===================== STEP 4 - OLLAMA CHECK =====================
echo   !C_CYN![4/6]!C_RST! Verifying AI Engine (Ollama)...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo     !C_YLW![!] Ollama disconnected. Local AI suspended.!C_RST!
    echo     !C_YLW!Install manually from ollama.com for full capability.!C_RST!
) else (
    echo     !C_GRN![✓] Neural engine linked.!C_RST!
)
echo.

:: ===================== STEP 5 - SILENT LAUNCHER =====================
echo   !C_CYN![5/6]!C_RST! Configuring Stealth Protocols...

if not exist .env (
    (
        echo TELEGRAM_TOKEN=PASTE_TOKEN_HERE
        echo MODEL_NAME=qwen2.5-coder:7b
    ) > .env
    echo     !C_YLW![!] .env generated. TELEGRAM_TOKEN REQUIRED.!C_RST!
)

(
    echo Set WshShell = CreateObject^("WScript.Shell"^)
    echo WshShell.Run chr^(34^) ^& "%~dp0start_zyron.bat" ^& chr^(34^), 0
    echo Set WshShell = Nothing
) > run_silent.vbs

echo     !C_GRN![✓] Stealth launcher primed.!C_RST!
echo.

:: ===================== STEP 6 - AUTO-START SETUP =====================
echo   !C_CYN![6/6]!C_RST! Finalizing Startup Sequence...

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

:: Cleanup old entries
if exist "%STARTUP_FOLDER%\PikachuAgent.lnk" del "%STARTUP_FOLDER%\PikachuAgent.lnk" >nul 2>&1
if exist "%STARTUP_FOLDER%\ZyronAssistant.lnk" del "%STARTUP_FOLDER%\ZyronAssistant.lnk" >nul 2>&1

echo.
echo     !C_CYN![?] SYSTEM PROMPT:!C_RST!
echo     !C_BCYN!Activate automatic resonance on PC boot?!C_RST!
echo.
choice /c YN /m "     Enable Autostart? "

if errorlevel 2 (
    echo.
    echo     !C_YLW![-] Startup resonance bypassed.!C_RST!
    goto :FinishSetup
)

echo.
echo     !C_CYN![+] Deploying startup artifact...!C_RST!

(
    echo Set WshShell = WScript.CreateObject^("WScript.Shell"^)
    echo Set oShellLink = WshShell.CreateShortcut^("%STARTUP_FOLDER%\ZyronAssistant.lnk"^)
    echo oShellLink.TargetPath = "%~dp0run_silent.vbs"
    echo oShellLink.WorkingDirectory = "%~dp0"
    echo oShellLink.Description = "Zyron Desktop Assistant - Auto Start"
    echo oShellLink.IconLocation = "shell32.dll,137"
    echo oShellLink.Save
) > create_startup_shortcut.vbs

cscript //nologo create_startup_shortcut.vbs
del create_startup_shortcut.vbs

if exist "%STARTUP_FOLDER%\ZyronAssistant.lnk" (
    echo     !C_GRN![✓] Autostart successfully armed!!C_RST!
) else (
    echo     !C_YLW![!] Warning: Shortcut deployment failed.!C_RST!
)

:FinishSetup
echo.
echo   !C_CYN!  ══════════════════════════════════════════════════
echo                !C_BCYN!✅ SYSTEM READY — ZYRON ACTIVE!C_RST!
echo     ══════════════════════════════════════════════════!C_RST!
echo.
echo   !C_BCYN!  🎯 MISSION PARAMETERS:!C_RST!
echo   !C_CYN!  ──────────────────────────────────────────────────!C_RST!

call :Typewriter "   - Credentials: Check .env for Telegram Token"
call :Typewriter "   - Quick Launch: Run run_silent.vbs"
call :Typewriter "   - Management: Rerun setup to reconfigure"

echo   !C_CYN!  ──────────────────────────────────────────────────!C_RST!
echo.
pause
exit /b

:Typewriter
set "text=%~1"
powershell -NoProfile -Command "$text='%text%'; for ($i=0; $i -lt $text.Length; $i++) { Write-Host $text[$i] -ForegroundColor Cyan -NoNewline; Start-Sleep -Milliseconds 15 }"
echo.
exit /b