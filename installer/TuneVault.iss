#define MyAppName "TuneVault"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TuneVault"
#define MyAppExeName "TuneVault.exe"
#define MyAppIconName "tunevault.ico"

[Setup]
AppId={{8E1C455E-7782-47F3-9DB2-3DC66A5E94FE}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\TuneVault
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..
OutputBaseFilename=TuneVault_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=tunevault.ico
UninstallDisplayIcon={app}\{#MyAppIconName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\TuneVault.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "tunevault.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppIconName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
