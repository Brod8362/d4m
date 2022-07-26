@echo off
if exist C:\Windows\System32\libarchive.dll (
	set libarchive=1
	echo Libarchive already installed.
) else (
	set libarchive=0
	echo Temporarily installing libarchive...
	copy windows/libarchive.dll C:\Windows\System32\libarchive.dll
)

echo Installing build dependencies...
python -m pip install .
python -m pip install pyinstaller libarchive

echo Building exe bundle...
pyinstaller --clean --onefile --noconsole --add-data windows\libarchive.dll;. src\d4m\gui.py -n d4m.exe --icon=resources\logo.ico 

echo Building executable installer...
"%PROGRAMFILES(x86)%\NSIS\makensis.exe" install_windows.nsi

if %libarchive%==0 (
	echo Removing libarchive
	del C:\Windows\System32\libarchive.dll
)
pause