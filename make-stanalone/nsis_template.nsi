; NSIS Script
Outfile "{OutputFileName}"
InstallDir $TEMP\{MyAppName}
RequestExecutionLevel user
SilentInstall silent
SetCompressor /SOLID /FINAL lzma
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
  ExecShell "open" "$INSTDIR\pythonw.exe" "$INSTDIR\main.pyc --release --app_version {MyAppVersion}"

SectionEnd
