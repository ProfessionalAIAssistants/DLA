# DLA File Organization Summary

## Main Folder (Essential Files Only)
The main folder now contains only the essential files needed to run the application:

### Application Files
- `app.py` - Main application entry point
- `crm_app.py` - Core Flask application 
- `.env.template` - Environment variable template

### Directories
- `config/` - Configuration files (settings.json, config.json, etc.)
- `data/` - Database and data files
- `docs/` - Documentation files
- `logs/` - Log files (crm_app.log moved here)
- `scripts/` - Utility and maintenance scripts
- `src/` - Source code modules
- `web/` - Web templates and static files
- `Layout/` - Project layout documentation
- `.git/` - Git repository files

## Files Moved to `scripts/` Folder
All utility and maintenance scripts have been moved to keep the main folder clean:

### Database Scripts
- `analyze_templates.py` - Template analysis utility
- `check_db.py` - Database verification
- `cleanup_database.py` - Database cleanup tool
- `clear_both_dbs.py` - Clear multiple databases
- `clear_business_data.py` - Business data cleanup
- `clear_business_data_auto.py` - Automated business data cleanup
- `compare_db.py` - Database comparison tool
- `database_analysis.py` - Comprehensive database analysis
- `database_cleanup_final.py` - Final cleanup script
- `database_verification.py` - Database integrity verification
- `db_analysis.py` - Database analysis tool
- `remove_backup_tables.py` - Backup table removal

### Import Cleanup Scripts
- `clean_crm_data_imports.py` - CRM data import cleanup
- `clean_dibbs_imports.py` - DIBBs import cleanup
- `clean_imports.py` - General import cleanup

### Test Scripts
- `test_config.py` - Configuration testing
- `test_db_connection.py` - Database connection testing

### Batch Files (Existing)
- `run_diagnostics.bat` - System diagnostics
- `run_parser.bat` - Parser execution
- `run_processor.bat` - PDF processor execution

### Other Utilities
- `start_crm.py` - Application startup script
- `validate_setup.py` - Setup validation

## Files Removed (Duplicates)
- `codebase_analysis.md` - Duplicate removed (exists in docs/)
- `settings.json` - Duplicate removed (exists in config/)

## Configuration Updates
Updated configuration files to reflect new file locations:
- `config/config.json` - Log file path updated to `logs/crm_app.log`
- `config/settings.production.json` - Log file path updated to `logs/crm_app.log`
- `src/pdf/dibbs_crm_processor.py` - Settings file path updated to `config/settings.json`

## Benefits of This Organization
1. **Clean Main Directory** - Only essential application files remain
2. **Logical Grouping** - Related files are organized together
3. **Easier Maintenance** - Scripts are separated from core application
4. **Better Navigation** - Clear folder structure for different file types
5. **Production Ready** - Clean structure suitable for deployment

## Usage
- To run the application: `python app.py`
- To run maintenance scripts: `cd scripts && python script_name.py`
- To view documentation: Check the `docs/` folder
- To check logs: Check the `logs/` folder
