; Inno Setup 6 — genera build\out\WhisperPRO-Setup-<version>.exe
; Asistente: Bienvenida → Licencia → Carpeta → Opciones → Instalar → Abrir WhisperPRO
; La clave de IA ya no se pide acá: al abrir la app por primera vez, la conexión guiada la consigue y la detecta sola.
#define AppName "WhisperPRO"
#define AppVersion GetEnv("WP_VERSION")
#if AppVersion == ""
  #define AppVersion "6.15.0"
#endif
#define AppPublisher "FESTUDIOS"
#define AppExe "WhisperPRO.exe"

[Setup]
AppId={{7E2B1C44-6D1A-4A0B-9C3B-5A1E0F3D2B71}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://festudios.pro
AppSupportURL=mailto:festudioarg@gmail.com
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
OutputDir=out
OutputBaseFilename={#AppName}-Setup-{#AppVersion}
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
SetupIconFile=..\logo.ico
LicenseFile=..\LICENCIA.txt
CloseApplications=force
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Instalador de {#AppName}
VersionInfoCopyright=© 2026 {#AppPublisher}
VersionInfoVersion={#AppVersion}

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "startup"; Description: "Iniciar {#AppName} con Windows (recomendado)"; GroupDescription: "Opciones:"
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Opciones:"; Flags: unchecked

[Files]
Source: "..\dist\WhisperPRO\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; configuración del usuario: solo se crea la primera vez (las actualizaciones no la pisan)
Source: "..\.env.example"; DestDir: "{userappdata}\WhisperPRO"; DestName: ".env"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Configuración de {#AppName}"; Filename: "{userappdata}\WhisperPRO\.env"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: startup

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName} ahora"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/f /im {#AppExe}"; Flags: runhidden; RunOnceId: "CerrarApp"

[Code]
function InitializeSetup(): Boolean;
var
  Code: Integer;
begin
  { si hay una versión abierta, la cerramos para poder actualizar }
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/f /im {#AppExe}', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := True;
end;
