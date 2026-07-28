@echo off
echo Clearing old build
rmdir /s /q "./dist/"
echo Building OctoPy for windows
pyinstaller --onefile --log-level ERROR --noconsole --name="OctoPy" main.py
echo Build complete
echo Transfering ROMS
xcopy ".\roms" ".\dist\roms" /I
xcopy ".\testroms" ".\dist\testroms" /I