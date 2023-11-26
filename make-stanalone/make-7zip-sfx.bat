@echo off

set SEVENZIPEXE=..\..\7zip\7zr.exe
set SEVENSFXMOD=..\..\7zip\7zSD.sfx
set WINRESEXE=..\..\go-winres.exe

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
rem python "./compile_and_collect.py"
rem Create the 7Zip archive
copy "%PROJECTDIR%\ReleaseInfo.txt" "%PROJECTDIR%\release\ReleaseInfo.txt"
rem "%SEVENZIPEXE%" a -y -mx9 -m0=LZMA2 "%OUTPUTDIR%\Installer.7z" "%PROJECTDIR%\release"

rem Create the SFX archive by concatenating the SFX module, the config file and the 7Zip archive
copy /b "%SEVENSFXMOD%" + "7zip_sfx_options.txt" + "%OUTPUTDIR%\Installer.7z" "%OUTPUTDIR%\%SFXName%"
rem Create manifest and patch the Executable
python "./create_manifest.py"
%WINRESEXE% patch "%OUTPUTDIR%\%SFXName%"
rem Display a message when the SFX archive is created
echo The SFX archive %SFXName% has been created successfully.
