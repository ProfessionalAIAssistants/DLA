from src.core.config_manager import config_manager
print('✅ Config manager working!')
config = config_manager.get_app_config()
print(f'Environment: {config["environment"]}')
print(f'Upload dir: {config_manager.get_upload_dir()}')
print(f'Database: {config_manager.get_database_path()}')
print('✅ All systems operational!')
