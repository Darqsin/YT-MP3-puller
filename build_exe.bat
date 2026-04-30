@echo off
setlocal
cd /d "%~dp0"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --windowed --onefile --name TuneVault tunevault.py
if errorlevel 1 pause && exit /b 1
echo.
echo EXE created at: dist\TuneVault.exe
pause
