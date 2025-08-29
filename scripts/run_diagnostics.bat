@echo off
cd /d "%~dp0\.."
echo ===================================
echo DLA CRM System Diagnostic
echo ===================================
echo Running tests on %date% at %time%
echo Current directory: %cd%
echo.

echo Step 1: Testing CRM App Import...
python -c "import sys; sys.path.insert(0, 'src'); from core.crm_app import app; print('✅ CRM App loads successfully')"
echo.

echo Step 2: Testing Database Connection...
python -c "import sys; sys.path.insert(0, 'src'); from core import crm_data; accounts = crm_data.crm_data.get_accounts(); print(f'✅ Database connected - {len(accounts)} accounts found')"
echo.

echo Step 3: Testing PDF Processor...
python -c "import sys; sys.path.insert(0, 'src'); from pdf.dibbs_crm_processor import DIBBsCRMProcessor; processor = DIBBsCRMProcessor(); print('✅ PDF processor loads successfully')"
echo.

echo All diagnostic tests completed.
echo.
pause
