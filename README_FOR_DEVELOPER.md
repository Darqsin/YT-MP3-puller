# TuneVault Windows Installer Builder

This folder is for the developer, not the end user.

## What the end user should receive

Only this file:

```text
TuneVault_Setup.exe
```

The end user should not install Python, yt-dlp, ffmpeg, pip packages, PyInstaller, or Inno Setup.

## Why the setup EXE is not already inside this zip

This ChatGPT environment is Linux-based and cannot compile a real Windows installer directly. The package includes two ways to generate the installer on Windows.

## Best option: GitHub Actions builds it automatically

1. Put these files in a GitHub repo.
2. Go to **Actions**.
3. Run **Build Windows Installer**.
4. Download the artifact named **TuneVault_Setup**.
5. Give only `TuneVault_Setup.exe` to users.

## Local Windows build option

On your developer computer only:

1. Install Python.
2. Install Inno Setup 6.
3. Double-click `build_installer.bat`.
4. Give only `TuneVault_Setup.exe` to users.

## End-user instructions

1. Double-click `TuneVault_Setup.exe`.
2. Click Next / Install.
3. Open TuneVault.

No CMD. No PATH. No manual ffmpeg. No manual yt-dlp.
