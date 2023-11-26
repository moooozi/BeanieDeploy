; NSIS Script
Outfile "{OutputFileName}"
InstallDir $TEMP\{MyAppName}
RequestExecutionLevel user
SilentInstall silent

Icon "{IconPath}"

; Metadata


; Pages
Page directory
Page instfiles

; Sections
Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  File /r "{SourcePath}\interpreter\*"
  File /r "{SourcePath}\src\*"
  ExecShell "open" "$INSTDIR\interpreter\pythonw.exe" "$INSTDIR\src\main.pyc"

SectionEnd
