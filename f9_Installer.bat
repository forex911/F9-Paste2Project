@echo off
title F9 CLI Installer (Stable)

echo Installing F9 CLI...

:: Use user-safe directory
set "INSTALL_DIR=%LOCALAPPDATA%\f9"

:: Create folder
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy python file
copy /Y "%~dp0f9.py" "%INSTALL_DIR%\f9.py" >nul

:: Create wrapper
echo @echo off > "%INSTALL_DIR%\f9.bat"
echo python "%INSTALL_DIR%\f9.py" %%* >> "%INSTALL_DIR%\f9.bat"

echo Created command at %INSTALL_DIR%

:: Get current PATH safely
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%B"

:: Check if already exists
echo %CURRENT_PATH% | find /i "%INSTALL_DIR%" >nul
if errorlevel 1 (
    echo Adding to PATH...

    if defined CURRENT_PATH (
        setx PATH "%CURRENT_PATH%;%INSTALL_DIR%" >nul
    ) else (
        setx PATH "%INSTALL_DIR%" >nul
    )

    echo ✅ PATH updated
) else (
    echo ⚠️ Already in PATH
)

:: Check Python
where python >nul 2>nul
if errorlevel 1 (
    echo ⚠️ Python not found in PATH
    echo Please install Python or add it to PATH
)

echo.
echo ✅ INSTALL COMPLETE
echo Restart terminal and run: f9
pause