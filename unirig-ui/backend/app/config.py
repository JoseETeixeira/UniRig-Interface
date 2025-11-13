"""
Configuration loader for UniRig UI backend.
Loads settings from config.yaml and provides them as Pydantic models.
"""

import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import Optional


class SystemConfig(BaseModel):
    """System-level configuration."""
    python_version: str
    cuda_version: str
    gpu_available: bool
    gpu_name: Optional[str] = None


class PathsConfig(BaseModel):
    """File path configuration."""
    project_root: str
    model_checkpoint: str
    upload_dir: str
    results_dir: str


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1


class CeleryConfig(BaseModel):
    """Celery task queue configuration."""
    broker_url: str
    result_backend: str


class Config(BaseModel):
    """Complete application configuration."""
    system: SystemConfig
    paths: PathsConfig
    server: ServerConfig
    celery: CeleryConfig


def load_config(config_path: str = "config.yaml") -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml file (relative to project root)
    
    Returns:
        Config object with all settings
    
    Raises:
        FileNotFoundError: If config.yaml doesn't exist
        ValueError: If config.yaml is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Please run install.sh to generate config.yaml"
        )
    
    try:
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return Config(**config_data)
    
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to parse config file: {e}")


# Global settings instance (loaded on import)
try:
    settings = load_config()
except FileNotFoundError:
    # If config doesn't exist, use defaults (for testing)
    settings = Config(
        system=SystemConfig(
            python_version="3.11",
            cuda_version="12.1",
            gpu_available=False
        ),
        paths=PathsConfig(
            project_root="/app",
            model_checkpoint="/root/.cache/huggingface/hub",
            upload_dir="./uploads",
            results_dir="./results"
        ),
        server=ServerConfig(),
        celery=CeleryConfig(
            broker_url="redis://redis:6379/0",
            result_backend="redis://redis:6379/0"
        )
    )
