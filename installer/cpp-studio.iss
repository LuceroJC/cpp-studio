; installer/cpp-studio.iss
#define MyAppName "CPP Studio"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "<Your Name / Lab>"
#define MyAppURL "https://github.com/<you>/cpp-studio"
#define MyAppExeName "cppstudio-app.exe"

[Setup]
AppId={{07D1CDB8-8E2B-4A8D-9D1F-7E2A0B2E0A10}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={commonpf64}\CPP Studio
DefaultGroupName=CPP Studio
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir=Output
OutputBaseFilename=cpp-studio-{#MyAppVersion}-setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
LicenseFile=..\docs\EULA.md
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "addpath"; Description: "Add CPP Studio to PATH (command line)"; GroupDescription: "Additional tasks:"; Flags: unchecked

[Files]
; Pull from PyInstaller dist at repo root
Source: "..\dist\cpp-studio\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\CPP Studio"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\CPP Studio (Batch Report)"; Filename: "{app}\cpps-report.exe"; Parameters: "--help"
Name: "{group}\Uninstall CPP Studio"; Filename: "{uninstallexe}"
Name: "{commondesktop}\CPP Studio"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch CPP Studio"; Flags: nowait postinstall skipifsilent

[Registry]
; Optional PATH addition (requires admin)
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; \
    ValueType: expandsz; ValueName: "Path"; \
    ValueData: "{olddata};{app}"; Tasks: addpath; Check: IsAdmin
