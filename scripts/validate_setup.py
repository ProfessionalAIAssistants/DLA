#!/usr/bin/env python3
"""
DLA CRM Configuration Validation Script
Validates that all configuration and paths are properly set up
"""

import sys
import json
from pathlib import Path

def validate_config():
    """Validate configuration manager and paths"""
    print("🔧 Validating DLA CRM Configuration...")
    
    try:
        # Import config manager
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from core.config_manager import config_manager
        
        print("✅ Config manager imported successfully")
        
        # Check directory structure
        directories = {
            'Base Directory': config_manager.get_base_dir(),
            'Config Directory': config_manager.get_config_dir(),
            'Data Directory': config_manager.get_data_dir(),
            'Upload Directory': config_manager.get_upload_dir(),
            'Processed Directory': config_manager.get_processed_dir(),
            'Output Directory': config_manager.get_output_dir(),
        }
        
        print("\n📁 Directory Structure:")
        all_exist = True
        for name, path in directories.items():
            exists = "✅" if path.exists() else "❌"
            print(f"  {exists} {name}: {path}")
            if not path.exists():
                all_exist = False
        
        # Check configuration files
        print("\n⚙️ Configuration Files:")
        config_files = {
            'Main Config': config_manager.get_config_dir() / 'config.json',
            'Settings': config_manager.get_config_dir() / 'settings.json',
            'Production Settings': config_manager.get_config_dir() / 'settings.production.json',
            'Environment Template': config_manager.get_base_dir() / '.env.template',
        }
        
        for name, path in config_files.items():
            exists = "✅" if path.exists() else "❌"
            print(f"  {exists} {name}: {path}")
        
        # Test configuration loading
        print("\n🔄 Testing Configuration Loading:")
        try:
            app_config = config_manager.get_app_config()
            print(f"  ✅ Environment: {app_config.get('environment', 'Not set')}")
            print(f"  ✅ Debug mode: {app_config.get('debug', 'Not set')}")
            print(f"  ✅ Database path: {app_config.get('database_path', 'Not set')}")
        except Exception as e:
            print(f"  ❌ Configuration loading error: {e}")
        
        # Create missing directories
        if not all_exist:
            print("\n🔨 Creating missing directories...")
            config_manager.ensure_directories()
            print("  ✅ Directories created")
        
        print("\n🎉 Validation complete!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def validate_database():
    """Validate database configuration"""
    print("\n💾 Validating Database Configuration...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from core.crm_database import db
        
        # Test database connection
        test_query = "SELECT name FROM sqlite_master WHERE type='table'"
        tables = db.execute_query(test_query)
        
        print(f"  ✅ Database connected successfully")
        print(f"  ✅ Tables found: {len(tables)}")
        
        # List main tables
        main_tables = ['accounts', 'contacts', 'opportunities', 'rfqs']
        for table_name in main_tables:
            table_exists = any(table['name'] == table_name for table in tables)
            status = "✅" if table_exists else "❌"
            print(f"    {status} {table_name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 DLA CRM System Validation")
    print("=" * 50)
    
    config_ok = validate_config()
    db_ok = validate_database()
    
    print("\n" + "=" * 50)
    if config_ok and db_ok:
        print("🎉 All systems validated successfully!")
        print("✅ Ready for development/production use")
    else:
        print("⚠️  Some issues found - please review above")
        
    print("\n📚 Next steps:")
    print("  1. Copy .env.template to .env and configure")
    print("  2. Update production settings in config/settings.production.json")
    print("  3. Run the application: python crm_app.py")

if __name__ == "__main__":
    main()
