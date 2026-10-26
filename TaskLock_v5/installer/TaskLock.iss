; TaskLock v5 BLUECORE — user-level Windows setup using Inno Setup 6
#ifndef MyAppVersion
  #define MyAppVersion "5.0.0"
#endif
#define MyAppName "TaskLock"
#define MyAppPublisher "Tavlokyn Studios"

[Setup]
AppId={{21F5F18B-E418-4EAC-856C-4403E4F9CB45}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName=TaskLock v{#MyAppVersion} BLUECORE
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\TaskLock
DefaultGroupName=TaskLock
UninstallDisplayIcon={app}\TaskLock.exe
OutputDir=..\release
OutputBaseFilename=TaskLock-v{#MyAppVersion}-Setup
SetupIconFile=..\assets\tasklock.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
MinVersion=10.0
ChangesAssociations=no
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
Source: "..\dist\TaskLock.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Browser_Extension\*"; DestDir: "{app}\Browser_Extension"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\TaskLock"; Filename: "{app}\TaskLock.exe"
Name: "{autodesktop}\TaskLock"; Filename: "{app}\TaskLock.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TaskLock.exe"; Description: "Launch TaskLock"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; User data is intentionally NOT deleted from %APPDATA%\TaskLock.
