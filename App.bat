@echo off
rem set the variables
set PYTHONPATH=%~dp0src
set builtin_python_path=interpreter\python\pythonw.exe
set main_script="%~dp0src\main.py"

rem check if bundled python exists
if exist %builtin_python_path% (
    echo Running with bundled python
    %builtin_python_path% %main_script%
    exit /b 0
)
rem check if system python 3 is installed
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    echo Running with system python 3
    pythonw %main_script%
    exit /b 0
)
rem ask the user if they want to install python
color 0A
set /p choice=Python 3 is not installed. Python is a required dependency for this App to work. Do you want to install it from Microsoft Store? (y/n)
if /i "%choice%" equ "y" (
	color 07
    echo Installing python 3
    Powershell -Command "winget install python3 --accept-source-agreements --accept-package-agreements"
    echo Running with system python 3
    pythonw %main_script%
    exit /b 0
) else (
    echo Python 3 is required to run this App. Please install it manually and try again.
    exit /b 1
)