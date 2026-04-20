@echo off
echo ==============================================
echo   AETHER OS - STARTUP INITIALIZATION (¬‿¬)
echo ==============================================
echo.

:: Try to remove the old Task Scheduler task if it exists to avoid conflicts
schtasks /delete /tn "AetherOSDaemon" /f >nul 2>&1

set "SCRIPT_PATH=%~dp0main.py"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "VBS_PATH=%STARTUP_FOLDER%\AetherDaemon.vbs"

echo Creating persistent background startup hook...

echo Set WshShell = CreateObject("WScript.Shell") > "%VBS_PATH%"
echo WScript.Sleep 10000 >> "%VBS_PATH%"
echo WshShell.Run "cmd /c cd /d ""%~dp0"" && python main.py", 0, False >> "%VBS_PATH%"

echo.
echo ✅ Aether is now fully registered in your User Startup folder!
echo This fixes the background/admin UAC isolation so vision works properly!
echo Please restart your PC to witness the seamless auto-boot!
echo.
pause
