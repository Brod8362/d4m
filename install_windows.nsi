!include Library.nsh

# if you're looking at this, please understand i am a linux user and have no idea what i'm doing!
OutFile "d4m_install.exe"

InstallDir $PROGRAMFILES\d4m

Section

SetOutPath $INSTDIR

File dist\d4m.exe
File resources\logo.svg

CreateShortcut "$SMPROGRAMS\d4m.lnk" "$INSTDIR\d4m.exe"
WriteUninstaller $INSTDIR\uninstall.exe


SectionEnd

Section "Uninstall"

Delete $INSTDIR\d4m.exe
Delete $INSTDIR\logo.svg

SectionEnd