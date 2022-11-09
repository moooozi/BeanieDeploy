@echo off
set PYTHONPATH=%~dp0src
set builtin_python_path=interpreter\python\pythonw.exe
set main_script="%~dp0src\main.py"
if exist %builtin_python_path% (
	echo Python exists
	@start "" %builtin_python_path% %main_script%
) else (
	echo Python not found, downloading
	echo:
	echo:
	echo:
	python3.11 --version >NUL
	if errorlevel 1 (
		start /b /wait interpreter\install.bat
	)
	@start "" pythonw3.11 %main_script%
)