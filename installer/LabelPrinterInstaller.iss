[Setup]
AppName=Label Printer
AppVersion=1.0.0
DefaultDirName={pf}\LabelPrinter
DefaultGroupName=Label Printer
UninstallDisplayIcon={app}\LabelPrinter.exe
OutputBaseFilename=LabelPrinterSetup
OutputDir=Output
Compression=lzma
SolidCompression=yes

[Files]
Source: "..\dist_windows\LabelPrinter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__"
Source: "..\label_size.txt"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{src}\..\label_size.txt'))

[Icons]
Name: "{group}\Label Printer"; Filename: "{app}\LabelPrinter.exe"
Name: "{group}\Uninstall Label Printer"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\LabelPrinter.exe"; Description: "Label Printer 실행"; Flags: nowait postinstall skipifsilent

