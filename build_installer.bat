@echo off
setlocal
cd /d "%~dp0"
call build_exe.bat
if errorlevel 1 exit /b 1
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
  echo Inno Setup is not installed on this developer computer.
  echo Install it from https://jrsoftware.org/isinfo.php then run this again.
  pause
  exit /b 1
)
%ISCC% installer\TuneVault.iss
if errorlevel 1 pause && exit /b 1
echo.
echo Installer created: TuneVault_Setup.exe
echo Give ONLY TuneVault_Setup.exe to the end user.
pause
