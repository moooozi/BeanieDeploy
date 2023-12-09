@echo off

set WINRAREXE=..\..\winrar\WinRAR.exe

set PROJECTDIR=..
set OUTPUTDIR=%PROJECTDIR%\output

rem Read the app name and version from the ReleaseInfo.txt file
for /f "tokens=1,2 delims=: " %%a in (..\ReleaseInfo.txt) do (
  if "%%a"=="AppName" set AppName=%%b
  if "%%a"=="AppVersion" set AppVersion=%%b
)
rem Create the SFX archive name using the app name and version
set SFXName=%AppName%-v%AppVersion%-Bundled-Win64.exe
rem Check if file exists
if exist "%OUTPUTDIR%\%SFXName%" del "%OUTPUTDIR%\%SFXName%"
rem Run compile collect script
python "./compile_and_collect.py"
rem Run the WinRAR command to create the SFX archive
copy "%PROJECTDIR%\ReleaseInfo.txt" "%PROJECTDIR%\release\ReleaseInfo.txt"
"%WINRAREXE%" a -sfx -s -md32m -m3 -iicon"%PROJECTDIR%\src\resources\style\app-icon.ico" -k -z"winrar_sfx_options.txt" "%OUTPUTDIR%\%SFXName%" "%PROJECTDIR%\release"
rem Display a message when the SFX archive is created
echo The SFX archive %SFXName% has been created successfully.
