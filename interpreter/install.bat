@echo off
python3.11 --version >NUL
if errorlevel 1 (
	Powershell -Command "winget install 'python 3.11' --source msstore --accept-source-agreements --accept-package-agreements" >NUL
)