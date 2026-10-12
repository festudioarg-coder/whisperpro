; Inno Setup 6 — genera build\out\WhisperPRO-Setup-<version>.exe
; Asistente: Bienvenida → Licencia → Carpeta → Opciones → Clave de IA → Instalar → Abrir WhisperPRO
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
var
  KeyPage: TInputQueryWizardPage;

function InitializeSetup(): Boolean;
var
  Code: Integer;
begin
  { si hay una versión abierta, la cerramos para poder actualizar }
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/f /im {#AppExe}', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := True;
end;

procedure InitializeWizard();
begin
  KeyPage := CreateInputQueryPage(wpSelectTasks,
    'Clave de IA (opcional)',
    'Si no la tenés, dejá esto vacío y seguí.',
    'Al abrir {#AppName} te guiamos paso a paso para conseguirla gratis en un minuto:' + #13#10 +
    'la copiás en la web de Groq y {#AppName} la detecta sola.' + #13#10 +
    'Si ya tenías {#AppName} instalado, dejalo vacío y se mantiene la que tenías.');
  KeyPage.Add('GROQ_API_KEY:', False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Key, EnvFile: String;
begin
  if CurStep = ssPostInstall then
  begin
    Key := Trim(KeyPage.Values[0]);
    if Key <> '' then
    begin
      EnvFile := ExpandConstant('{userappdata}\WhisperPRO\.env');
      { la última línea gana al leer el .env: así no hace falta editar el archivo }
      SaveStringToFile(EnvFile, #13#10 + 'GROQ_API_KEY=' + Key + #13#10, True);
    end;
  end;
end;
