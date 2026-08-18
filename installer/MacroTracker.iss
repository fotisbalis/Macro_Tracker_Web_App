[Setup]
AppId={{3D3050EA-4F2F-4EAF-9A11-BD05C2B8F2F7}
AppName=Macro Tracker
AppVersion=1.0.0
AppPublisher=Macro Tracker
DefaultDirName={localappdata}\Programs\Macro Tracker
DefaultGroupName=Macro Tracker
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=MacroTracker-Setup-1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\macro-tracker.ico
UninstallDisplayIcon={app}\Macro Tracker.exe
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\Macro Tracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Macro Tracker"; Filename: "{app}\Macro Tracker.exe"
Name: "{autodesktop}\Macro Tracker"; Filename: "{app}\Macro Tracker.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\Macro Tracker.exe"; Description: "Launch Macro Tracker"; Flags: nowait postinstall skipifsilent
