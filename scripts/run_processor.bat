@echo off
echo Running DLA PDF Processor...
cd /d "%~dp0"
cd ..
python -c "import sys; sys.path.insert(0, 'src'); from pdf.dibbs_crm_processor import DIBBsCRMProcessor; processor = DIBBsCRMProcessor(); result = processor.process_all_pdfs(); print(f'Processed: {result[\"processed\"]}, Created: {result[\"created\"]}, Skipped: {result[\"skipped\"]}')"
echo.
echo Press any key to exit...
pause > nul
