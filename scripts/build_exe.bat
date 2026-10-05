@echo off
cd /d "%~dp0\.."
echo Сборка Timer.exe через PyInstaller...
py -m PyInstaller --onefile --noconsole --name "Timer" --distpath ".\dist" --workpath ".\build" --paths ".\src" run.py
echo.
echo Сборка завершена! Исполняемый файл доступен в dist\Timer.exe
pause
