@echo off
cd /d "%~dp0\.."
echo Сборка Just Timer.exe через PyInstaller с иконкой...
py -m PyInstaller --onefile --noconsole --name "Just Timer" --icon="assets\icon.ico" --add-data="assets;assets" --distpath ".\dist" --workpath ".\build" --paths ".\src" run.py
echo.
echo Сборка завершена! Исполняемый файл доступен в dist\Just Timer.exe
pause
