@echo off

set path=%path%;%cd%\windows

echo Installing build dependencies...
python -m pip install .
python -m pip install pyinstaller libarchive

echo Building exe bundle...
pyinstaller --clean --onefile --noconsole --add-data windows\libarchive.dll;. src\d4m\gui.py -n d4m.exe --icon=resources\logo.ico 

echo Building executable installer...
"%PROGRAMFILES(x86)%\NSIS\makensis.exe" install_windows.nsi