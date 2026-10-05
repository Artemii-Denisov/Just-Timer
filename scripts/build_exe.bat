@echo off
cd /d "%~dp0\.."
echo Сборка Just Timer.exe через PyInstaller...
py -m PyInstaller --onefile --noconsole --name "Just Timer" --distpath ".\dist" --workpath ".\build" --paths ".\src" run.py
echo.
echo Сборка завершена! Исполняемый файл доступен в dist\Just Timer.exe
pause
