@echo off
title Installation raccourci San Giorgio
set "ROOT=%~dp0"
set "ICO=%ROOT%sangiorgio.ico"
set "BAT=%ROOT%lancer.bat"
set "DESKTOP=%USERPROFILE%\Desktop"

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP%\San Giorgio - OMS.lnk'); $s.TargetPath = '%BAT%'; $s.WorkingDirectory = '%ROOT%'; $s.IconLocation = '%ICO%, 0'; $s.Description = 'Lancer San Giorgio OMS'; $s.Save()"

echo.
echo Raccourci "San Giorgio - OMS" cree sur le bureau !
echo.
pause
