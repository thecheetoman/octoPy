@echo off
:menu
cls
echo ======= OctoPy Build Menu =======
echo 1. Build for Windows
echo 2. WASM Web Packaging
echo 3. Exit

:: /C specifies the allowed keys. /M specifies the prompt message string.
choice /c 123 /m "Enter your choice: "

:: Note: Check %ERRORLEVEL% from HIGHEST value to LOWEST value.
if errorlevel 3 goto option3
if errorlevel 2 goto option2
if errorlevel 1 goto option1

:option1
echo Clearing old build
rmdir /s /q "./dist/"
echo Building OctoPy for windows
pyinstaller --onefile --log-level ERROR --noconsole --name="OctoPy" main.py
echo Build complete
echo Transfering ROMS
xcopy ".\roms" ".\dist\roms" /I
xcopy ".\testroms" ".\dist\testroms" /I
goto menu

:option2
echo doing nothing
goto menu

:option3
echo Exiting...
pause
exit