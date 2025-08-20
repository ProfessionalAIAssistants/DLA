@echo off
echo Running DLA PDF Processor...
cd /d "%~dp0"
python simplified_dla_processor.py -v
echo.
echo Press any key to exit...
pause > nul
