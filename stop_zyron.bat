@echo off
title 🛑 Stopping Zyron...
color 0C

echo.
echo    [!] Killing all Zyron processes...
echo.

:: Kill Python (The Brain)
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul

:: Kill Native Host if stuck (optional, usually managed by Firefox)
:: But good cleanup mechanism

echo.
echo    [✓] Zyron has been stopped.
echo    [i] To restart, double-click 'start_zyron.bat'
echo.
pause
