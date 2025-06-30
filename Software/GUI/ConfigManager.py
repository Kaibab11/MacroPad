import json
from pathlib import Path
from typing import List, Optional

class ConfigManager:
    """Manage configuration files"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".macropad_configs"
        self.config_dir.mkdir(exist_ok=True)
    
    def save_config(self, name: str, config: dict) -> bool:
        """Save a configuration to file"""
        try:
            config_file = self.config_dir / f"{name}.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def load_config(self, name: str) -> Optional[dict]:
        """Load a configuration from file"""
        try:
            config_file = self.config_dir / f"{name}.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return None
    
    def list_configs(self) -> List[str]:
        """List all available configurations"""
        configs = []
        for file in self.config_dir.glob("*.json"):
            configs.append(file.stem)
        return sorted(configs)
    
    def delete_config(self, name: str) -> bool:
        """Delete a configuration file"""
        try:
            config_file = self.config_dir / f"{name}.json"
            if config_file.exists():
                config_file.unlink()
                return True
        except Exception as e:
            print(f"Error deleting config: {e}")
        return False