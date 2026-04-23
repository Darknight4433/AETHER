@echo off
setlocal

cd /d "%~dp0"

echo.
echo [1/3] Installing packaging tools...
python -m pip install --upgrade pip >nul
python -m pip install pyinstaller >nul
if errorlevel 1 (
    echo Failed to install PyInstaller.
    exit /b 1
)

echo.
echo [2/3] Building Aether executable...
if exist build rmdir /s /q build
if exist dist\Aether.exe del /q dist\Aether.exe
if exist dist_installer rmdir /s /q dist_installer

pyinstaller --noconfirm --clean Aether.spec
if errorlevel 1 (
    echo PyInstaller build failed.
    exit /b 1
)

echo.
echo [3/3] Building Inno Setup installer...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not defined ISCC (
    echo Inno Setup 6 was not found.
    echo Install it from https://jrsoftware.org/isinfo.php and rerun this script.
    echo The packaged EXE is ready at dist\Aether.exe
    exit /b 0
)

"%ISCC%" "installer\Aether.iss"
if errorlevel 1 (
    echo Inno Setup build failed.
    exit /b 1
)

echo.
echo Build complete.
echo EXE: dist\Aether\Aether.exe
echo Installer: dist_installer\AetherSetup.exe
endlocal
