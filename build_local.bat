@echo off
setlocal
cd /d "%~dp0"

python -m pip install -r requirements.txt
if errorlevel 1 pause & exit /b 1

pyinstaller TuneVault.spec
if errorlevel 1 pause & exit /b 1

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "TuneVault.iss"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    "C:\Program Files\Inno Setup 6\ISCC.exe" "TuneVault.iss"
) else (
    echo Inno Setup not found. Install Inno Setup 6, then run this again.
    pause
    exit /b 1
)

pause
