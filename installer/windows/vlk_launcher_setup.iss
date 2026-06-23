; VLK Launcher - Script d'installation Inno Setup
; Créé par yolezz pour VOLKZ Clan

#define AppName "VLK Launcher"
#define AppVersion "1.0.0"
#define AppPublisher "VOLKZ Clan"
#define AppExeName "VLKLauncher.exe"
#define AppAssocName "VLK Launcher"
#define AppAssocExt ".vlk"

[Setup]
; Informations de base
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={commonpf}\VLKLauncher
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=installer\windows\output
OutputBaseFilename=VLKLauncher-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
WizardImageFile=installer\windows\setup_wizard.bmp
WizardSmallImageFile=installer\windows\setup_small.bmp
SetupIconFile=..\src\client\assets\icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
AppCopyright=© 2024 VOLKZ Clan - Créé par yolezz
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Licences
LicenseFile=installer\windows\license.txt

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Languages\English.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "Icônes supplémentaires:"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "Icônes supplémentaires:"; OnlyBelowVersion: 6.1
Name: "startup"; Description: "Lancer au démarrage"; GroupDescription: "Options:"

[Files]
; Fichiers principaux de l'application (embarqués dans l'installateur)
Source: "..\dist\windows\VLKLauncher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Icône Bureau
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Run]
; Lancer l'application après installation
Filename: "{app}\{#AppExeName}"; Description: "Lancer {#AppName}"; Flags: nowait postinstall skipifsilent

[Registry]
; Enregistrement pour la désinstallation
Root: HKLM; Subkey: "Software\VOLKZ Clan\VLKLauncher"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKLM; Subkey: "Software\VOLKZ Clan\VLKLauncher"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"

[UninstallDelete]
; Supprimer tous les fichiers lors de la désinstallation
Type: filesandordirs; Name: "{app}\*"
Type: dirifempty; Name: "{app}"

[Code]
// Fonction pour vérifier si une instance est déjà en cours d'exécution
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // Vérifier si l'application est déjà installée
  if RegKeyExists(HKEY_LOCAL_MACHINE, 'Software\VOLKZ Clan\VLKLauncher') then
  begin
    if MsgBox('VLK Launcher est déjà installé. Voulez-vous le désinstaller avant la nouvelle installation?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Lancer le désinstallateur
      if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\VOLKZ Clan\VLKLauncher', 'UninstallString', '') then
      begin
        Exec(ExpandConstant('{reg:HKLM\Software\VOLKZ Clan\VLKLauncher,UninstallString}'), '/SILENT', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
      end;
    end;
  end;
end;

// Personnalisation de la page de fin
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Créer un fichier de marqueur pour l'installation réussie
    SaveStringToFile(ExpandConstant('{app}\.installed'), 'Install successful', False);
  end;
end;
