# Tests Directory

This directory contains test files, debugging utilities, and development scripts for the DLA CRM system.

## File Categories

### Test Files (`test_*.py`)
- `test_contact_opps.py` - Tests for contact-opportunity relationships
- `test_create_task_direct.py` - Direct task creation tests
- `test_db_insert.py` - Database insertion tests
- `test_existing_nsn.py` - NSN existence validation tests
- `test_mfr_fix.py` - Manufacturer parsing fix tests
- `test_nsn_display.py` - NSN display functionality tests
- `test_part_extraction.py` - Part number extraction tests
- `test_pdf_integration.py` - PDF processing integration tests
- `test_pdf_qpl_integration.py` - PDF-QPL integration tests
- `test_pdf_updates.py` - PDF update functionality tests
- `test_qpl_creation.py` - QPL creation tests
- `test_task_api.py` - Task API endpoint tests
- `test_task_filtering.py` - Task filtering tests

### Database Check Files (`check_*.py`)
- `check_account.py` - Account data validation
- `check_contact.py` - Contact data validation
- `check_db_structure.py` - Database structure verification
- `check_nsn.py` - NSN data validation
- `check_opportunities.py` - Opportunities data validation
- `check_opp_columns.py` - Opportunity column validation
- `check_schema.py` - Database schema validation
- `check_tables.py` - Table structure validation
- `check_task_linking.py` - Task linking validation

### Debug Files (`debug_*.py`)
- `debug_mfr_extraction.py` - Manufacturer extraction debugging
- `debug_nsn_join.py` - NSN join operation debugging

### Utility Files
- `add_pdf_path_column.py` - Database column addition script
- `add_test_opportunities.py` - Test data creation script
- `analyze_pdf_lines.py` - PDF line analysis utility
- `create_qpl_tables.py` - QPL table creation script
- `quick_db_check.py` - Quick database status check
- `verify_updates.py` - Update verification utility

## Usage

These files are primarily for development and testing purposes. They are not part of the main application runtime but are useful for:

1. **Testing new features** before integration
2. **Debugging issues** in production
3. **Database maintenance** and validation
4. **Development utilities** for data manipulation

To run any test file:
```bash
python tests/test_filename.py
```

To run database checks:
```bash
python tests/check_filename.py
```
