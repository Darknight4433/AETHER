[Setup]
AppId={{4F87F493-C5D8-4F7E-8D55-0A5939A407D3}
AppName=Aether
AppVersion=1.0.0
AppPublisher=Aether Systems
DefaultDirName={localappdata}\Programs\Aether
DefaultGroupName=Aether
UninstallDisplayIcon={app}\Aether.exe
OutputDir=..\dist_installer
OutputBaseFilename=AetherSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startup"; Description: "Launch Aether when I sign in"; GroupDescription: "Startup:"; Flags: checkedonce

[Files]
Source: "..\dist\Aether\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{userappdata}\Aether"
Name: "{userappdata}\Aether\assets"
Name: "{userappdata}\Aether\voice_profiles"

[Icons]
Name: "{group}\Aether"; Filename: "{app}\Aether.exe"
Name: "{autodesktop}\Aether"; Filename: "{app}\Aether.exe"; Tasks: desktopicon
Name: "{userstartup}\Aether"; Filename: "{app}\Aether.exe"; Tasks: startup

[Run]
Filename: "{app}\Aether.exe"; Description: "Launch Aether"; Flags: nowait postinstall skipifsilent
