@echo off
if exist interpreter\python\ (
	echo Python exists

	@start "" "interpreter\python\pythonw.exe" "src\main.py"
	goto :EOF
) else (
	echo Python not found, downloading
	echo:
	echo:
	echo:
	call interpreter\install.bat && @start "" "pythonw" "src\main.py" && goto :EOF
)
