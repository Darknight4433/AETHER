@echo off
title Aether OS - Installer
color 0A
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║       AETHER OS - ONE CLICK SETUP        ║
echo  ║         Context-Aware AI Assistant        ║
echo  ╚══════════════════════════════════════════╝
echo.

:: ─── Step 1: Check Python ───
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python is not installed or not in PATH.
    echo  Please install Python 3.10+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
echo        Python found.
echo.

:: ─── Step 2: Install Dependencies ───
echo [2/4] Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r "%~dp0requirements.txt" --quiet
if errorlevel 1 (
    echo  WARNING: Some packages may have failed. Retrying...
    python -m pip install -r "%~dp0requirements.txt"
)
echo        Dependencies installed.
echo.

:: ─── Step 3: Check FFmpeg ───
echo [3/4] Checking FFmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo        WARNING: FFmpeg not found. Speech-to-Text will be limited.
    echo        Install from: https://ffmpeg.org/download.html
) else (
    echo        FFmpeg found.
)
echo.

:: ─── Step 4: Setup Autostart ───
echo [4/4] Registering startup service...

:: Remove old scheduled task if exists
schtasks /delete /tn "AetherOSDaemon" /f >nul 2>&1

set "SCRIPT_DIR=%~dp0"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_PATH=%STARTUP_FOLDER%\AetherDaemon.vbs"

:: Create the VBS launcher
echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_PATH%"
echo WScript.Sleep 10000 >> "%VBS_PATH%"
echo WshShell.Run "cmd /c cd /d ""%SCRIPT_DIR%"" && python main.py", 0, False >> "%VBS_PATH%"

echo        Startup service registered.
echo.

:: ─── Done ───
echo  ╔══════════════════════════════════════════╗
echo  ║            SETUP COMPLETE                 ║
echo  ╠══════════════════════════════════════════╣
echo  ║  Aether will auto-start on next login.   ║
echo  ║                                          ║
echo  ║  To start NOW, run:                      ║
echo  ║    python main.py                        ║
echo  ║                                          ║
echo  ║  Hotkeys:                                ║
echo  ║    Ctrl+Alt+A  = Wake Aether             ║
echo  ║    Ctrl+Alt+P  = Toggle Panel            ║
echo  ║    Ctrl+Alt+S  = Screenshot              ║
echo  ║    Ctrl+Alt+M  = Mute                    ║
echo  ╚══════════════════════════════════════════╝
echo.
pause
