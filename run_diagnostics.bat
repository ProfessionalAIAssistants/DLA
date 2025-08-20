@echo off
echo ===================================
echo DLA PDF Processing Diagnostic Suite
echo ===================================
echo Running tests on %date% at %time%
echo.

echo Step 1: Checking Database Tables...
py test_db_tables.py
echo.

echo Step 2: Checking PDF Processing Setup...
py test_pdf_count.py
echo.

echo Step 3: Validating DIBBs Script...
py test_dibbs_script.py
echo.

echo All diagnostic tests completed.
echo.
pause
