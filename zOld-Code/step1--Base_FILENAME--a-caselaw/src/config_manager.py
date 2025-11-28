"""
Configuration manager for caselaw renamer.
Handles persistent settings like default registry path.
"""

import json
from pathlib import Path


class ConfigManager:
    """Manage application configuration settings."""

    def __init__(self, config_path=None):
        """
        Initialize config manager.

        Args:
            config_path: Optional path to config file (default: .caselaw_config.json in project root)
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default: look for config in project root (parent of src/)
            src_dir = Path(__file__).parent
            project_root = src_dir.parent
            self.config_path = project_root / '.caselaw_config.json'

    def load_config(self):
        """
        Load configuration from file.

        Returns:
            dict: Configuration dictionary, or empty dict if file doesn't exist
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                # If corrupted, return empty config
                return {}
        return {}

    def save_config(self, config):
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary to save

        Returns:
            bool: True if successful
        """
        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_default_registry_path(self):
        """
        Get default registry path from config.

        Returns:
            str: Default registry path, or None if not set
        """
        config = self.load_config()
        return config.get('default_registry_path')

    def set_default_registry_path(self, path):
        """
        Set default registry path in config.

        Args:
            path: Path to set as default (string or Path object)

        Returns:
            bool: True if successful
        """
        config = self.load_config()
        config['default_registry_path'] = str(path)
        return self.save_config(config)

    def get_config_value(self, key, default=None):
        """
        Get a configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        config = self.load_config()
        return config.get(key, default)

    def set_config_value(self, key, value):
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set

        Returns:
            bool: True if successful
        """
        config = self.load_config()
        config[key] = value
        return self.save_config(config)
