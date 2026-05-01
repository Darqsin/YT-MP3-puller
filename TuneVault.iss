#define MyAppName "TuneVault"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "TuneVault"
#define MyAppExeName "TuneVault.exe"

[Setup]
AppId={{8E14DF9D-7B98-4F0B-B3AF-6F9B7C8E5D21}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=TuneVault_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=tunevault.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
Source: "dist\TuneVault.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "tunevault.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "fonts\*"; DestDir: "{app}\fonts"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: FontsFolderExists

[Icons]
Name: "{group}\TuneVault"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\tunevault.ico"
Name: "{autodesktop}\TuneVault"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\tunevault.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch TuneVault"; Flags: nowait postinstall skipifsilent

[Code]
function FontsFolderExists: Boolean;
begin
  Result := DirExists(ExpandConstant('{src}\fonts'));
end;
