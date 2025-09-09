"""
Configuration Manager
====================

Centralized configuration management for the DLA CRM application.
Handles loading configuration files, managing paths, and environment settings.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

class ConfigManager:
    """Manages application configuration files and settings"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.base_dir / 'config'
        self.data_dir = self.base_dir / 'data'
        self._config_cache = {}
        self._setup_environment()
        
    def _setup_environment(self):
        """Setup environment-specific configurations"""
        self.environment = os.getenv('DLA_ENV', 'development')
        self.debug_mode = self.environment == 'development'
        
    def get_base_dir(self) -> Path:
        """Get the base directory path"""
        return self.base_dir
        
    def get_config_dir(self) -> Path:
        """Get the config directory path"""
        return self.config_dir
        
    def get_data_dir(self) -> Path:
        """Get the data directory path"""
        return self.data_dir
        
    def get_upload_dir(self) -> Path:
        """Get the upload directory path"""
        return self.data_dir / 'upload' / 'To Process'
        
    def get_processed_dir(self) -> Path:
        """Get the processed files directory path"""
        return self.data_dir / 'processed' / 'Reviewed'
        
    def get_output_dir(self) -> Path:
        """Get the output directory path"""
        return self.data_dir / 'output'
        
    def get_database_path(self) -> Path:
        """Get the database file path"""
        return self.data_dir / 'crm.db'
        
    def load_config(self, config_name: str = 'config.json', use_cache: bool = True) -> Dict[str, Any]:
        """Load a configuration file with caching"""
        if use_cache and config_name in self._config_cache:
            return self._config_cache[config_name]
            
        config_path = self.config_dir / config_name
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    if use_cache:
                        self._config_cache[config_name] = config_data
                    return config_data
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading config {config_name}: {e}")
            
        return {}
    
    def load_settings(self) -> Dict[str, Any]:
        """Load application settings"""
        settings = self.load_config('settings.json')
        # Merge with environment-specific settings if they exist
        env_settings = self.load_config(f'settings.{self.environment}.json')
        settings.update(env_settings)
        return settings
    
    def load_email_config(self) -> Dict[str, Any]:
        """Load email configuration"""
        # Try multiple possible locations
        for possible_path in [
            self.base_dir / 'src' / 'email_automation' / 'email_config.json',
            self.base_dir / 'src' / 'email' / 'email_config.json',
            self.config_dir / 'email_config.json'
        ]:
            if possible_path.exists():
                try:
                    with open(possible_path, 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logging.error(f"Error loading email config from {possible_path}: {e}")
        
        return {}
    
    def save_config(self, data: Dict[str, Any], config_name: str = 'config.json') -> bool:
        """Save a configuration file"""
        try:
            config_path = self.config_dir / config_name
            self.config_dir.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
            # Update cache
            self._config_cache[config_name] = data
            return True
        except IOError as e:
            logging.error(f"Error saving config {config_name}: {e}")
            return False
    
    def save_settings(self, data: Dict[str, Any]) -> bool:
        """Save application settings"""
        return self.save_config(data, 'settings.json')
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get complete application configuration"""
        config = {
            'environment': self.environment,
            'debug': self.debug_mode,
            'database_path': str(self.get_database_path()),
            'upload_dir': str(self.get_upload_dir()),
            'processed_dir': str(self.get_processed_dir()),
            'output_dir': str(self.get_output_dir()),
            'base_dir': str(self.base_dir),
        }
        
        # Merge with file-based config
        file_config = self.load_config()
        config.update(file_config)
        
        # Add settings
        settings = self.load_settings()
        config['settings'] = settings
        
        return config
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.config_dir,
            self.data_dir,
            self.get_upload_dir(),
            self.get_processed_dir(),
            self.get_output_dir(),
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def clear_cache(self):
        """Clear the configuration cache"""
        self._config_cache.clear()

# Create global instance
config_manager = ConfigManager()
